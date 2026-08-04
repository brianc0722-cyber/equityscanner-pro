# EquityScanner Pro Dashboard

Beautiful, modular Streamlit frontend for the real-time scanner and pre-market engine.

## Quick Start

```bash
cd /home/user/stock_scanner
pip install -r requirements.txt          # or just streamlit + pandas + numpy
streamlit run dashboard/app.py
```

The dashboard runs fully in **demo mode** (no API keys required).

## Features

- Pre-market prediction engine (uses real `PreMarketSpeculationEngine` when available)
- Live quote + technicals display
- Full structured EquityReport generation
- Sector news insights with example bullish/bearish themes
- Clean tabbed layout for easy extension

## Adding New Features

The dashboard is intentionally modular:

- Each major section is a function (`render_*`)
- Tab 4 is reserved for "Live / Advanced"
- All data flows through `get_demo_pre_market_features` + `generate_demo_report`

Easy places to extend:
- Connect real `AsyncDataIngestor` WebSocket callbacks
- Add a multi-ticker scanner table
- Add historical accuracy backtesting tab
- Add scheduled pre-market batch simulation

## Integration with Backend

- Same dataclasses and engines as the core package
- Can call the FastAPI `/report` and `/premarket/predict` endpoints instead of local functions if you prefer microservice architecture
