"""
Demo data seeder for the API.
Call this on startup (or manually) so that /premarket/predict and /report
return meaningful data even without live streams.

Used to make the "Quick Start" experience excellent.
"""
from datetime import datetime, timedelta
from processing.live_processor import LiveMarketProcessor
from utils.models import Bar, Quote

async def seed_demo_pre_market_data(processor: LiveMarketProcessor, ticker: str = "AAPL"):
    """Seed realistic pre-market bars and a quote so the engine has data."""
    now = datetime.utcnow()
    
    # Simulate ~35 minutes of 1-min pre-market bars (plenty of data)
    base_price = 226.50 if ticker == "AAPL" else (118.30 if ticker == "NVDA" else 248.70)
    bars = []
    volume_base = 14000
    
    for i in range(35):
        ts = now - timedelta(minutes=40 - i)   # older timestamps
        drift = i * 0.09
        price = base_price + drift + (i % 4) * 0.07
        vol = int(volume_base * (0.9 + (i % 7) * 0.18))
        
        bar = Bar(
            ticker=ticker,
            open=round(price - 0.18, 2),
            high=round(price + 0.32, 2),
            low=round(price - 0.25, 2),
            close=round(price, 2),
            volume=vol,
            vwap=round(price, 2),
            timestamp=ts,
            interval="1m"
        )
        bars.append(bar)
        await processor.on_bar(bar.__dict__)
    
    # Current quote
    last_bar = bars[-1]
    quote = Quote(
        ticker=ticker,
        bid=round(last_bar.close - 0.04, 2),
        ask=round(last_bar.close + 0.05, 2),
        bid_size=2100,
        ask_size=1480,
        timestamp=now
    )
    await processor.on_quote(quote.__dict__)
    
    await processor.on_trade({
        "ticker": ticker,
        "price": last_bar.close,
        "size": 380,
        "timestamp": now
    })
    
    print(f"   Seeded {len(bars)} pre-market bars for {ticker}")
    return len(bars)

async def seed_multiple_tickers(processor: LiveMarketProcessor):
    """Seed data for the main tickers shown in the dashboard."""
    for tkr in ["AAPL", "NVDA", "TSLA", "MSFT"]:
        await seed_demo_pre_market_data(processor, tkr)
