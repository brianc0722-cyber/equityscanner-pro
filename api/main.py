"""
FastAPI Async API Layer.
- Live data search & quotes
- On-demand reports
- Sector news insights
- Pre-market predictions
Uses dependency injection for core engines.
"""
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

# Prometheus metrics
try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
    
    REQUEST_COUNT = Counter("equityscanner_requests_total", "Total requests", ["endpoint"])
    PREDICTION_TIME = Histogram("equityscanner_prediction_seconds", "Time spent on pre-market predictions")
    REPORT_TIME = Histogram("equityscanner_report_seconds", "Time spent generating reports")
except ImportError:
    PROMETHEUS_AVAILABLE = False
    REQUEST_COUNT = None
    PREDICTION_TIME = None
    REPORT_TIME = None

# Logging
from utils.logging import logger

# Robust imports that work both as package and with PYTHONPATH=.
import sys
from pathlib import Path

# Ensure the project root is in path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import config
from utils.models import EquityReport, SectorNewsInsight
from ingestion.data_ingestor import AsyncDataIngestor
from processing.live_processor import LiveMarketProcessor
from nlp.sentiment_engine import SentimentEngine
from premarket.speculation_engine import PreMarketSpeculationEngine
from reporting.report_generator import ReportGenerator

app = FastAPI(
    title="EquityScanner Pro - Real-Time Stock Analytics Engine",
    version="1.2.0",
    description="Scalable real-time scanner with pre-market predictive analytics"
)

# Global singletons (in prod: use lifespan + DI container)
ingestor: Optional[AsyncDataIngestor] = None
processor: Optional[LiveMarketProcessor] = None
sentiment_engine: Optional[SentimentEngine] = None
premarket_engine: Optional[PreMarketSpeculationEngine] = None
report_generator: Optional[ReportGenerator] = None

async def get_ingestor():
    global ingestor
    if ingestor is None:
        ingestor = AsyncDataIngestor()
        await ingestor.__aenter__()
    return ingestor

async def get_processor():
    global processor
    if processor is None:
        processor = LiveMarketProcessor()
        await processor.connect()
        # Seed demo data on first access if not already seeded
        try:
            from .seed_demo import seed_multiple_tickers
            await seed_multiple_tickers(processor)
        except Exception:
            pass
    return processor

async def get_sentiment():
    global sentiment_engine
    if sentiment_engine is None:
        sentiment_engine = SentimentEngine()
    return sentiment_engine

async def get_premarket():
    global premarket_engine
    if premarket_engine is None:
        premarket_engine = PreMarketSpeculationEngine()
    return premarket_engine

async def get_report_generator():
    global report_generator
    if report_generator is None:
        ing = await get_ingestor()
        proc = await get_processor()
        sent = await get_sentiment()
        prem = await get_premarket()
        report_generator = ReportGenerator(ing, proc, sent, prem)
    return report_generator

# Helper to convert dataclasses to JSON-serializable dict
def _to_serializable(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_serializable(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj

# === Pydantic Models for API ===
class TickerSearchResponse(BaseModel):
    tickers: List[str]
    query: str

class QuoteResponse(BaseModel):
    ticker: str
    price: float
    bid: float
    ask: float
    spread_pct: float
    volume: int
    timestamp: str

class PreMarketPredictionResponse(BaseModel):
    ticker: str
    volatility_score: float
    directional_score: float
    predicted_direction: str
    confidence: float
    expected_move_pct: float
    key_drivers: List[str]

class ReportResponse(BaseModel):
    report: dict  # Full EquityReport serialized

class SectorInsightResponse(BaseModel):
    insight: dict

# === Endpoints ===

@app.on_event("startup")
async def startup():
    """Pre-seed demo data so the pre-market engine and reports work immediately."""
    global processor
    try:
        if processor is None:
            processor = LiveMarketProcessor()
            await processor.connect()
        
        # Seed realistic pre-market data for the demo tickers
        # Import here to avoid circular issues
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from seed_demo import seed_multiple_tickers
        await seed_multiple_tickers(processor)
        print("✅ Demo pre-market data seeded successfully")
    except Exception as e:
        print(f"Demo seeding skipped (will use demo mode): {e}")

@app.on_event("shutdown")
async def shutdown():
    global ingestor, processor
    if ingestor:
        await ingestor.__aexit__(None, None, None)
    if processor:
        await processor.disconnect()

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "1.2.0"}

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(503, "Prometheus client not installed")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/search", response_model=TickerSearchResponse)
async def search_equities(
    q: str = Query(..., min_length=1, max_length=40),
    limit: int = Query(15, ge=1, le=50),
    ing: AsyncDataIngestor = Depends(get_ingestor)
):
    """Live ticker/company name search via REST."""
    # Production: integrate with Polygon / FMP / Finnhub search endpoints
    # Simplified: return plausible tickers
    results = [q.upper()]
    if len(q) > 2:
        results.extend([f"{q.upper()}{i}" for i in range(1, min(4, limit))])
    return TickerSearchResponse(tickers=results[:limit], query=q)

@app.get("/quotes/{ticker}", response_model=QuoteResponse)
async def get_live_quote(
    ticker: str,
    ing: AsyncDataIngestor = Depends(get_ingestor),
    proc: LiveMarketProcessor = Depends(get_processor)
):
    """Real-time quote snapshot."""
    ticker = ticker.upper()
    try:
        quotes = await ing.fetch_quotes([ticker])
        if not quotes:
            raise HTTPException(404, "No quote data")
        q = quotes[0]
        
        tech = await proc.get_live_technicals(ticker)
        return QuoteResponse(
            ticker=ticker,
            price=tech.get("last_price", q.ask),
            bid=q.bid,
            ask=q.ask,
            spread_pct=tech.get("bid_ask_spread_pct", 0.0),
            volume=int(tech.get("relative_volume", 1) * 1500000),
            timestamp=q.timestamp.isoformat()
        )
    except Exception as e:
        raise HTTPException(503, detail=str(e))

@app.post("/report/{ticker}", response_model=ReportResponse)
async def generate_report(
    ticker: str,
    include_premarket: bool = True,
    gen: ReportGenerator = Depends(get_report_generator)
):
    """On-demand structured report (fundamentals + technical + sentiment + pre-market)."""
    ticker = ticker.upper()
    try:
        report = await gen.generate_full_report(ticker, include_premarket=include_premarket)
        
        serializable_report = _to_serializable(report)
        return ReportResponse(report=serializable_report)
    except Exception as e:
        raise HTTPException(500, detail=f"Report generation failed: {str(e)}")

@app.get("/premarket/predict/{ticker}", response_model=PreMarketPredictionResponse)
async def predict_premarket(
    ticker: str,
    proc: LiveMarketProcessor = Depends(get_processor),
    sent: SentimentEngine = Depends(get_sentiment),
    prem: PreMarketSpeculationEngine = Depends(get_premarket)
):
    """Direct pre-market speculation engine call."""
    ticker = ticker.upper()
    
    if REQUEST_COUNT:
        REQUEST_COUNT.labels(endpoint="/premarket/predict").inc()
    
    avg_vol = 1800000
    features = await proc.build_pre_market_features(ticker, prev_close=145.0, avg_daily_vol=avg_vol)
    
    if not features:
        raise HTTPException(404, "Insufficient pre-market data for ticker")
    
    sentiment = await sent.get_ticker_sentiment(ticker)
    features.news_sentiment = sentiment.score
    
    if PREDICTION_TIME:
        with PREDICTION_TIME.time():
            prediction = await prem.predict(features)
    else:
        prediction = await prem.predict(features)
    
    logger.info(f"Pre-market prediction for {ticker}: {prediction.predicted_direction} (conf={prediction.confidence:.2f})")
    return PreMarketPredictionResponse(**prediction.__dict__)

@app.get("/insights/sector/{sector}", response_model=SectorInsightResponse)
async def get_sector_insights(
    sector: str,
    sent: SentimentEngine = Depends(get_sentiment)
):
    """Industry news insights: aggregate bullish/bearish themes."""
    sector = sector.title()
    try:
        insight = await sent.get_sector_insights(sector)
        return SectorInsightResponse(insight=insight.__dict__)
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/live/technicals/{ticker}")
async def live_technicals(ticker: str, proc: LiveMarketProcessor = Depends(get_processor)):
    """Raw live metrics for dashboards."""
    ticker = ticker.upper()
    data = await proc.get_live_technicals(ticker)
    return data
