# EquityScanner Pro — System Architecture

**High-Performance Real-Time Stock Scanner & Predictive Analytics Engine**  
Lead Financial Engineer & AI Systems Architect design — 2026

## Overview
A modular, asynchronous, event-driven microservices-style architecture designed for:
- Sub-second live market data ingestion
- Real-time technical computation (VWAP, relative volume, spread)
- FinBERT-powered NLP sentiment at scale
- Statistical/ML pre-market speculation at 9:30 AM EST open
- On-demand structured reporting (fundamentals + technicals + sentiment + prediction)

## Core Layers (Text-Based Architecture Diagram)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT / DASHBOARD LAYER                     │
│  (FastAPI endpoints, WebSocket feeds, REST reports, real-time UI)   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS / WebSocket
┌───────────────────────────────▼─────────────────────────────────────┐
│                           API LAYER (FastAPI)                       │
│  • /search, /quotes, /report/{ticker}                               │
│  • /premarket/predict/{ticker}                                      │
│  • /insights/sector/{sector}                                        │
│  • Live technicals + health                                         │
│  Dependency injection of core engines                               │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────────┐     ┌────────────────────┐
│ INGESTION     │     │ PROCESSING        │     │ NLP + PREMARKET    │
│ LAYER         │     │ LAYER             │     │ LAYER              │
│               │     │                   │     │                    │
│ • AsyncData   │────▶│ • LiveMarket      │◀────│ • SentimentEngine  │
│   Ingestor    │     │   Processor       │     │   (FinBERT)        │
│ • Alpaca WS   │     │ • Redis state     │     │ • Sector Insights  │
│ • Polygon WS  │     │ • VWAP, RelVol    │     │                    │
│ • Finnhub REST│     │ • Spread, Imb.    │     │ • PreMarketSpec    │
│ • REST APIs   │     │                   │     │   Engine (Ridge)   │
│ (quotes/bars) │     │                   │     │                    │
└───────────────┘     └───────────────────┘     └────────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MESSAGE BUS & STATE LAYER                        │
│  • Kafka (topics: trade, quote, news)                               │
│  • Redis (live prices, technicals, caches)                          │
│  • Event callbacks for tight coupling or pub/sub                    │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                     DATA PROVIDERS (External)                       │
│  Alpaca Markets (WS + REST)  •  Polygon.io (WS + Tick)              │
│  Finnhub (News + REST)       •  Financial Modeling Prep (Fundamentals)│
│  Environment: ALPACA_*, POLYGON_*, FINNHUB_*, FMP_*                 │
└─────────────────────────────────────────────────────────────────────┘
```

## Recommended Modern Tooling
- **Async Runtime**: `asyncio` + `aiohttp` + `websockets`
- **API**: FastAPI (ASGI)
- **Streaming / Decoupling**: Kafka (aiokafka) + Redis (aioredis)
- **NLP**: FinBERT (`ProsusAI/finbert`) via `transformers`
- **ML / Pre-market**: scikit-learn (Ridge regression) + feature engineering
- **Data Models**: Python `dataclasses` + Pydantic (API)
- **Live Compute**: In-memory deques + Redis for hot state
- **Observability**: Structured logs + health endpoints (expandable with Prometheus)

## Data Flow Highlights
1. **Ingestion** → WebSocket + REST polling → Kafka topics + callback dispatch
2. **Processing** → LiveMarketProcessor consumes events → Computes VWAP, relative volume, spread, imbalance → Redis
3. **NLP** → News items → FinBERT batch inference → SentimentResult + Sector aggregates
4. **Pre-Market** → At ~9:20 AM: `build_pre_market_features()` + sentiment injection → Ridge model → `PreMarketPrediction`
5. **Reporting** → Orchestrates parallel fetches → Constructs rich `EquityReport`

## Scalability Notes
- Horizontal scaling via multiple worker instances behind a load balancer
- Kafka consumer groups for ingestion workers
- Redis cluster for shared state
- Model inference can be offloaded to separate microservice (Ray / vLLM / Triton)
- Pre-market predictions run in batch at fixed schedule (cron-like)

## Critical Design Choices
- **No blocking I/O** anywhere in hot path
- **Realistic pre-market features**:
  - VWAP (volume-weighted)
  - Relative volume (pre-market normalized)
  - Bid-ask spread expansion (%)
  - Order book imbalance
  - Overnight gap %
  - News sentiment score
- **FinBERT** chosen for domain-specific financial sentiment
- Environment-variable configuration only (no secrets in code)

## Modules
- `config.py`
- `utils/models.py` — all dataclasses
- `ingestion/data_ingestor.py`
- `processing/live_processor.py`
- `nlp/sentiment_engine.py`
- `premarket/speculation_engine.py`
- `reporting/report_generator.py`
- `api/main.py` — FastAPI entrypoint

This architecture supports 100k+ tickers at scale with proper horizontal scaling and rate-limit-aware ingestion.
