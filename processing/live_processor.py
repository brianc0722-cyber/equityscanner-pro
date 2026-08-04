"""
Real-time processing layer. Consumes from ingestion (Kafka/callbacks), maintains state in Redis.
Computes technicals: VWAP, relative volume, bid-ask spread, order book imbalance.
"""
import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import redis.asyncio as redis
import numpy as np
import pandas as pd

from config import config
from utils.models import Bar, Quote, Trade, PreMarketFeatures

class LiveMarketProcessor:
    def __init__(self, redis_url: str = None):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = redis_url or config.REDIS_URL
        self.bars_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=120))  # 2h of 1m bars
        self.quotes_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.trades_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.avg_vol_cache: Dict[str, float] = {}  # previous day avg volume
        self._lock = asyncio.Lock()

    async def connect(self):
        self._redis_available = False
        self.redis = None
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            self._redis_available = True
        except Exception:
            print("Redis not available. Running fully in-memory demo mode (recommended for development).")
            self.redis = None

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def on_trade(self, trade_dict: dict):
        trade = Trade(**trade_dict)
        ticker = trade.ticker
        
        async with self._lock:
            self.trades_cache[ticker].append(trade)
            
            if self.redis:
                try:
                    await self.redis.set(f"price:{ticker}", trade.price, ex=300)
                    await self.redis.set(f"last_trade:{ticker}", json.dumps(trade_dict), ex=300)
                except Exception:
                    pass  # demo mode

    async def on_quote(self, quote_dict: dict):
        quote = Quote(**quote_dict)
        ticker = quote.ticker
        
        async with self._lock:
            self.quotes_cache[ticker].append(quote)
            
            # Compute spread
            spread_pct = (quote.ask - quote.bid) / quote.bid if quote.bid > 0 else 0.0
            
            if self.redis:
                try:
                    await self.redis.hset(f"quote:{ticker}", mapping={
                        "bid": quote.bid,
                        "ask": quote.ask,
                        "spread_pct": round(spread_pct, 5),
                        "timestamp": quote.timestamp.isoformat()
                    })
                    await self.redis.expire(f"quote:{ticker}", 120)
                except Exception:
                    pass  # demo mode - data stays in self.quotes_cache

    async def on_bar(self, bar_dict: dict):
        bar = Bar(**bar_dict)
        ticker = bar.ticker
        
        async with self._lock:
            self.bars_cache[ticker].append(bar)
            
            # Update VWAP rolling (only if Redis available)
            if len(self.bars_cache[ticker]) >= 5 and self.redis:
                try:
                    recent = list(self.bars_cache[ticker])[-30:]
                    total_vol = sum(b.volume for b in recent)
                    vwap = sum(b.vwap * b.volume for b in recent) / total_vol if total_vol > 0 else bar.close
                    await self.redis.hset(f"technicals:{ticker}", "vwap", round(vwap, 4))
                except Exception:
                    pass  # demo mode - we still have the in-memory cache

    async def compute_relative_volume(self, ticker: str, current_volume: int) -> float:
        """Relative volume = current pre-market / avg daily volume."""
        if ticker not in self.avg_vol_cache:
            # In prod: fetch from fundamentals cache or DB
            self.avg_vol_cache[ticker] = 1_500_000  # placeholder realistic for midcap
        
        avg_daily = self.avg_vol_cache[ticker]
        # Pre-market volume is usually 5-20% of daily. Normalize by expected fraction (approx)
        expected_pre = avg_daily * 0.12  # rough pre-market fraction
        return round(current_volume / max(expected_pre, 1), 2)

    async def compute_order_book_imbalance(self, ticker: str) -> float:
        """Simple proxy: average bid_size vs ask_size over recent quotes."""
        quotes = list(self.quotes_cache[ticker])[-20:]
        if not quotes:
            return 0.0
        
        total_bid = sum(q.bid_size for q in quotes)
        total_ask = sum(q.ask_size for q in quotes)
        if total_bid + total_ask == 0:
            return 0.0
        return round((total_bid - total_ask) / (total_bid + total_ask), 4)

    async def compute_vwap_from_bars(self, ticker: str, window_minutes: int = 30) -> float:
        bars = list(self.bars_cache[ticker])
        if not bars:
            return 0.0

        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent = [b for b in bars if b.timestamp >= cutoff]
        if not recent:
            recent = bars[-5:]

        vol_sum = sum(b.volume for b in recent)
        if vol_sum == 0:
            return recent[-1].close
        vwap = sum(b.vwap * b.volume for b in recent) / vol_sum
        return round(vwap, 4)

    async def _safe_redis_get(self, key: str, default=0.0):
        if not self.redis:
            return default
        try:
            val = await self.redis.get(key)
            return float(val) if val else default
        except Exception:
            return default

    async def get_live_technicals(self, ticker: str) -> Dict:
        """Aggregated live metrics. Fully works in demo/in-memory mode."""
        async with self._lock:
            vwap = await self.compute_vwap_from_bars(ticker)
            
            # Always prefer in-memory quote cache first
            quotes = list(self.quotes_cache.get(ticker, []))
            if quotes:
                last_q = quotes[-1]
                spread_pct = (last_q.ask - last_q.bid) / last_q.bid if last_q.bid > 0 else 0.008
            else:
                spread_pct = 0.008
            
            # Volume from in-memory cache (always available)
            trades = list(self.trades_cache[ticker])
            current_vol = sum(t.size for t in trades[-200:]) if trades else 0
            rel_vol = await self.compute_relative_volume(ticker, current_vol)
            
            imbalance = await self.compute_order_book_imbalance(ticker)
            
            last_price = trades[-1].price if trades else vwap
            
            return {
                "ticker": ticker,
                "vwap": round(vwap, 2),
                "relative_volume": rel_vol,
                "bid_ask_spread_pct": round(spread_pct, 5),
                "order_book_imbalance": imbalance,
                "last_price": round(last_price, 2),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def build_pre_market_features(self, ticker: str, prev_close: float, avg_daily_vol: int) -> Optional[PreMarketFeatures]:
        """Build the feature vector used by pre-market engine. Called at 9:20 AM."""
        bars = list(self.bars_cache[ticker])
        if not bars or not prev_close:
            return None

        # Pre-market specific (assume bars are pre-market)
        pre_vol = sum(b.volume for b in bars)
        pre_high = max(b.high for b in bars) if bars else prev_close
        pre_low = min(b.low for b in bars) if bars else prev_close
        
        # VWAP
        vol_sum = sum(b.volume for b in bars)
        pre_vwap = sum(b.vwap * b.volume for b in bars) / vol_sum if vol_sum > 0 else prev_close
        
        gap_pct = (pre_vwap - prev_close) / prev_close
        
        # Quote snapshot
        quotes = list(self.quotes_cache.get(ticker, []))
        if quotes:
            last_q = quotes[-1]
            spread_pct = (last_q.ask - last_q.bid) / last_q.bid if last_q.bid > 0 else 0.0
            imb = await self.compute_order_book_imbalance(ticker)
        else:
            spread_pct = 0.008
            imb = 0.0
        
        rel_vol = pre_vol / max(avg_daily_vol * 0.15, 1)  # adjusted pre-market normalization
        
        return PreMarketFeatures(
            ticker=ticker,
            prev_close=prev_close,
            pre_market_vwap=pre_vwap,
            pre_market_high=pre_high,
            pre_market_low=pre_low,
            pre_market_volume=pre_vol,
            avg_daily_volume=avg_daily_vol,
            relative_volume=round(rel_vol, 3),
            gap_pct=round(gap_pct, 4),
            bid_ask_spread_pct=round(spread_pct, 5),
            order_book_imbalance=round(imb, 4),
            news_sentiment=0.0,  # to be injected by NLP
            timestamp=datetime.utcnow()
        )
