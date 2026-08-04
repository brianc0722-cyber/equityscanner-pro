import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Data Providers - Use env placeholders, no hard-coded keys
    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_API_SECRET: str = os.getenv("ALPACA_API_SECRET", "")
    POLYGON_API_KEY: str = os.getenv("POLYGON_API_KEY", "")
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")

    # Infrastructure
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

    # Market Times (America/New_York)
    PREMARKET_START_HOUR: int = 4
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 30
    MARKET_CLOSE_HOUR: int = 16

    # Pre-market speculation thresholds (realistic)
    REL_VOL_THRESHOLD: float = 2.5
    SPREAD_EXPANSION_THRESHOLD: float = 0.015  # 1.5% of price
    GAP_THRESHOLD: float = 0.03

    # NLP
    FINBERT_MODEL: str = "ProsusAI/finbert"
    SECTOR_NEWS_WINDOW_MINUTES: int = 120

    # ML / Predictive
    VOLATILITY_WINDOW: int = 30  # minutes pre-market
    MAX_PRE_MARKET_SAMPLES: int = 5000

config = Config()
