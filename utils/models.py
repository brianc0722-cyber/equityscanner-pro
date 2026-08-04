from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Literal
import numpy as np

@dataclass
class Quote:
    ticker: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    timestamp: datetime
    exchange: Optional[str] = None

@dataclass
class Trade:
    ticker: str
    price: float
    size: int
    timestamp: datetime
    conditions: List[str] = field(default_factory=list)

@dataclass
class Bar:
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float
    timestamp: datetime
    interval: str = "1m"

@dataclass
class NewsItem:
    ticker: str
    headline: str
    body: str
    published_at: datetime
    source: str
    url: Optional[str] = None
    sector: Optional[str] = None

@dataclass
class SentimentResult:
    ticker: str
    score: float  # -1.0 (bearish) to +1.0 (bullish)
    label: Literal["bearish", "neutral", "bullish"]
    confidence: float
    source_count: int
    timestamp: datetime

@dataclass
class PreMarketFeatures:
    ticker: str
    prev_close: float
    pre_market_vwap: float
    pre_market_high: float
    pre_market_low: float
    pre_market_volume: int
    avg_daily_volume: int
    relative_volume: float
    gap_pct: float
    bid_ask_spread_pct: float
    order_book_imbalance: float  # (bid_vol - ask_vol) / (bid_vol + ask_vol)
    news_sentiment: float
    timestamp: datetime

@dataclass
class PreMarketPrediction:
    ticker: str
    volatility_score: float  # 0-1 normalized expected volatility
    directional_score: float  # -1 to +1
    predicted_direction: Literal["down", "flat", "up"]
    confidence: float
    expected_move_pct: float  # e.g. +/- 1.8%
    key_drivers: List[str]
    timestamp: datetime

@dataclass
class TechnicalSummary:
    ticker: str
    vwap: float
    relative_volume: float
    rsi_14: Optional[float]
    macd_histogram: Optional[float]
    atr_14: Optional[float]
    support_levels: List[float]
    resistance_levels: List[float]

@dataclass
class FundamentalSummary:
    ticker: str
    market_cap: float
    pe_ratio: Optional[float]
    eps: Optional[float]
    revenue_growth: Optional[float]
    debt_to_equity: Optional[float]
    analyst_target: Optional[float]
    analyst_rating: Optional[str]

@dataclass
class EquityReport:
    ticker: str
    generated_at: datetime
    fundamental: FundamentalSummary
    technical: TechnicalSummary
    sentiment: SentimentResult
    premarket_prediction: Optional[PreMarketPrediction] = None
    summary_text: str = ""
    key_risks: List[str] = field(default_factory=list)
    recommendation: str = ""

@dataclass
class SectorNewsInsight:
    sector: str
    aggregate_sentiment: float
    bullish_themes: List[str]
    bearish_themes: List[str]
    top_headlines: List[str]
    news_count: int
    timestamp: datetime
