"""
Custom Reporting Module.
Generates on-demand structured equity reports: fundamentals + technicals + sentiment + pre-market prediction.
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional

from config import config
from utils.models import (
    EquityReport, FundamentalSummary, TechnicalSummary,
    SentimentResult, PreMarketPrediction, PreMarketFeatures
)
from processing.live_processor import LiveMarketProcessor
from nlp.sentiment_engine import SentimentEngine
from premarket.speculation_engine import PreMarketSpeculationEngine
from ingestion.data_ingestor import AsyncDataIngestor


class ReportGenerator:
    def __init__(self, 
                 ingestor: AsyncDataIngestor,
                 processor: LiveMarketProcessor,
                 sentiment_engine: SentimentEngine,
                 premarket_engine: PreMarketSpeculationEngine):
        self.ingestor = ingestor
        self.processor = processor
        self.sentiment = sentiment_engine
        self.premarket = premarket_engine

    async def generate_fundamental_summary(self, ticker: str) -> FundamentalSummary:
        """Fetch + normalize fundamentals. Graceful fallback in demo mode."""
        try:
            raw = await self.ingestor.fetch_fundamentals(ticker)
        except Exception:
            raw = None
        
        if not raw:
            # Realistic demo fundamentals
            demo_fund = {
                "AAPL": {"market_cap": 3450000000000, "pe": 34.2, "eps": 6.15, "revenue_growth": 0.062},
                "NVDA": {"market_cap": 2890000000000, "pe": 42.8, "eps": 2.88, "revenue_growth": 0.15},
            }.get(ticker, {"market_cap": 500000000000, "pe": 28.0, "eps": 4.2, "revenue_growth": 0.08})
            
            return FundamentalSummary(
                ticker=ticker,
                market_cap=demo_fund["market_cap"],
                pe_ratio=demo_fund["pe"],
                eps=demo_fund["eps"],
                revenue_growth=demo_fund["revenue_growth"],
                debt_to_equity=0.35,
                analyst_target=265.0 if ticker == "AAPL" else 142.0,
                analyst_rating="Buy"
            )
        
        return FundamentalSummary(
            ticker=ticker,
            market_cap=float(raw.get("marketCap", 0)),
            pe_ratio=raw.get("pe"),
            eps=raw.get("eps"),
            revenue_growth=raw.get("revenueGrowth"),
            debt_to_equity=raw.get("debtToEquity"),
            analyst_target=raw.get("targetHighPrice"),
            analyst_rating=raw.get("rating", "Hold")
        )

    async def generate_technical_summary(self, ticker: str) -> TechnicalSummary:
        """Real-time technical snapshot from processor."""
        tech = await self.processor.get_live_technicals(ticker)
        
        # Simple support/resistance derived from recent bars (production: use more sophisticated)
        bars = list(self.processor.bars_cache.get(ticker, []))[-30:]
        if bars:
            lows = sorted([b.low for b in bars])
            highs = sorted([b.high for b in bars])
            support = [round(lows[len(lows)//4], 2), round(lows[0], 2)]
            resistance = [round(highs[-len(highs)//4], 2), round(highs[-1], 2)]
        else:
            support, resistance = [tech["last_price"] * 0.98], [tech["last_price"] * 1.02]

        return TechnicalSummary(
            ticker=ticker,
            vwap=tech.get("vwap", tech["last_price"]),
            relative_volume=tech.get("relative_volume", 1.0),
            rsi_14=None,  # Could compute with TA-Lib or pandas-ta if installed
            macd_histogram=None,
            atr_14=None,
            support_levels=support,
            resistance_levels=resistance
        )

    async def generate_full_report(self, ticker: str, include_premarket: bool = True) -> EquityReport:
        """Main on-demand report generator. Async and comprehensive."""
        # Parallelize data fetching
        fund_task = asyncio.create_task(self.generate_fundamental_summary(ticker))
        tech_task = asyncio.create_task(self.generate_technical_summary(ticker))
        sent_task = asyncio.create_task(self.sentiment.get_ticker_sentiment(ticker))
        
        fundamental = await fund_task
        technical = await tech_task
        sentiment = await sent_task
        
        premarket_pred = None
        if include_premarket:
            # Build pre-market features using current state (live_processor)
            avg_vol = 2_000_000  # In prod: load from historical or fundamentals
            features = await self.processor.build_pre_market_features(
                ticker, prev_close=fundamental.market_cap / 1e9 if fundamental.market_cap > 0 else 120.0,
                avg_daily_vol=avg_vol
            )
            
            if features:
                # Inject latest sentiment
                features.news_sentiment = sentiment.score
                premarket_pred = await self.premarket.predict(features)
        
        # Narrative summary
        summary_text = self._build_narrative(ticker, fundamental, technical, sentiment, premarket_pred)
        
        # Risks
        risks = self._extract_risks(fundamental, technical, sentiment, premarket_pred)
        
        # Simple recommendation
        rec = self._generate_recommendation(sentiment, premarket_pred, technical)
        
        return EquityReport(
            ticker=ticker,
            generated_at=datetime.utcnow(),
            fundamental=fundamental,
            technical=technical,
            sentiment=sentiment,
            premarket_prediction=premarket_pred,
            summary_text=summary_text,
            key_risks=risks,
            recommendation=rec
        )

    def _build_narrative(self, ticker: str, fund: FundamentalSummary, tech: TechnicalSummary,
                         sent: SentimentResult, pred: Optional[PreMarketPrediction]) -> str:
        parts = [
            f"{ticker} trades {tech.relative_volume:.1f}x relative volume near VWAP ${tech.vwap:.2f}.",
            f"Market cap: ${fund.market_cap:,.0f}. "
        ]
        
        if fund.pe_ratio:
            parts.append(f"P/E {fund.pe_ratio:.1f}. ")
        
        if sent.label != "neutral":
            parts.append(f"News sentiment is {sent.label} ({sent.score:+.2f}). ")
        
        if pred:
            parts.append(f"Pre-market model signals {pred.predicted_direction.upper()} with {pred.confidence:.0%} confidence. "
                         f"Expected move: ±{pred.expected_move_pct:.1f}%. ")
            if pred.key_drivers:
                parts.append("Drivers: " + "; ".join(pred.key_drivers[:3]) + ".")
        
        return " ".join(parts)

    def _extract_risks(self, fund, tech, sent, pred) -> List[str]:
        risks = []
        if tech.relative_volume > 4.0:
            risks.append("Extremely elevated relative volume - potential reversal risk")
        if pred and pred.volatility_score > 0.65:
            risks.append(f"High pre-market volatility forecast ({pred.volatility_score:.0%})")
        if sent.label == "bearish" and sent.confidence > 0.6:
            risks.append("Negative news sentiment cluster")
        if fund.pe_ratio and fund.pe_ratio > 45:
            risks.append("Premium valuation (high P/E)")
        return risks or ["No major structural risks detected"]

    def _generate_recommendation(self, sent: SentimentResult, pred: Optional[PreMarketPrediction], tech: TechnicalSummary) -> str:
        """Pre-market direction now strongly drives the final recommendation (Recommendation #3)."""
        
        # Base score from sentiment
        score = sent.score
        
        # === Strong pre-market bias ===
        if pred:
            # Pre-market directional score has heavy weight
            score += pred.directional_score * 0.85
            
            # When pre-market has decent confidence, bias even more
            if pred.confidence > 0.60:
                if pred.predicted_direction == "up":
                    score += 0.35
                elif pred.predicted_direction == "down":
                    score -= 0.35
        
        # Final classification with pre-market priority
        if pred and pred.predicted_direction == "up" and pred.confidence >= 0.58:
            return "BULLISH - Strong pre-market momentum into open"
        elif pred and pred.predicted_direction == "down" and pred.confidence >= 0.58:
            return "BEARISH - Weak pre-market signals — caution or short bias"
        
        # Fallback blended logic
        if score > 0.42 and tech.relative_volume > 1.6:
            return "BULLISH - Strong momentum setup into open"
        elif score < -0.32:
            return "BEARISH - Caution or short bias"
        elif abs(score) < 0.18 and tech.relative_volume < 1.4:
            return "NEUTRAL - Wait for open confirmation"
        return "MIXED - Monitor first 15 minutes of trading"
