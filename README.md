# EquityScanner Pro

**Real-time Stock Scanner + Pre-Market Predictive Analytics Engine**

A complete, production-grade, asynchronous system with:
- Live market data ingestion (WebSocket + REST)
- Real-time technical processing (VWAP, relative volume, spread, imbalance)
- FinBERT-powered news sentiment + sector insights
- **Statistical/ML pre-market speculation engine** (realistic features)
- FastAPI backend
- Beautiful Streamlit dashboard with **Quick Start** button

## Quick Start (Recommended)

```bash
cd stock_scanner

# Install dependencies (one time)
pip install -r requirements.txt

# Launch everything together (FastAPI + Dashboard)
python run_all.py
```

Then open:
- **Dashboard**: http://localhost:8501
- **FastAPI docs**: http://localhost:8000/docs
- Click the big **🚀 RUN QUICK START** button in the sidebar

## What You Get

- Pre-market directional + volatility predictions at 9:30 AM open
- Full structured equity reports
- Rich sector news insights (example data included)
- Live trade stream simulation
- Multi-ticker scanner
- Real FastAPI backend integration (when running)

## Individual Services

```bash
# Only API
python run_all.py --api-only

# Only Dashboard
python run_all.py --dashboard-only

# Or manually
PYTHONPATH=. uvicorn api.main:app --port 8000 --reload
streamlit run dashboard/app.py --server.port 8501
```

## Key Features Already Implemented

1. **Live WebSocket Simulation** (Tab "Live + Scanner")
2. **Multi-Ticker Pre-Market Scanner**
3. **Real FastAPI Backend Integration** (dashboard auto-detects)
4. **Quick Start** — one-click full pipeline demo
5. **Backtest Tab** — Compares "Old" vs "New" (heavy pre-market weighting) logic with equity curves
6. **CLI** — `python -m cli predict AAPL`, `python -m cli report NVDA`, `python -m cli backtest`
7. **Observability** — Prometheus `/metrics` + structured logging

## Screenshots

### Dashboard Overview
![Dashboard](https://via.placeholder.com/800x450?text=EquityScanner+Dashboard)

### Backtest Tab (Old vs New Logic)
![Backtest](https://via.placeholder.com/800x450?text=Backtest+-+Old+vs+New+Logic)

### Pre-Market Prediction
![Prediction](https://via.placeholder.com/600x300?text=Pre-Market+Prediction)

> Replace placeholders with real screenshots when you run the app locally (`python run_all.py`).

## Architecture

See `ARCHITECTURE.md` for the full layered design.

## Next Steps / Extensibility

The codebase is deliberately modular. Easy to add:
- Real WebSocket connections to Alpaca/Polygon
- Historical backtesting of pre-market predictions
- Portfolio scanner
- Alerting / notifications
- Scheduled pre-market batch jobs

All core engines are importable and reusable.

## Environment Variables (for live data)

```bash
export ALPACA_API_KEY=...
export ALPACA_API_SECRET=...
export POLYGON_API_KEY=...
export FINNHUB_API_KEY=...
export FMP_API_KEY=...
export REDIS_URL=redis://localhost:6379/0
```

The system runs fully in demo mode without any keys.

## Project Structure

```
stock_scanner/
├── api/                    # FastAPI backend
├── dashboard/              # Streamlit UI + Quick Start
├── ingestion/              # Async data layer (WS + REST)
├── processing/             # Live technicals + Redis
├── nlp/                    # FinBERT sentiment
├── premarket/              # Speculation engine (core ML)
├── reporting/              # EquityReport generator
├── utils/models.py         # All dataclasses
├── run_all.py              # Unified launcher
└── ARCHITECTURE.md
```

Built as a Lead Financial Engineer + AI Systems Architect project.
