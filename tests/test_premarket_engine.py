import pytest
import asyncio
from datetime import datetime, timezone

from premarket.speculation_engine import PreMarketSpeculationEngine
from utils.models import PreMarketFeatures


def make_features(
    gap: float = 0.015,
    rel_vol: float = 2.3,
    news: float = 0.4,
    spread: float = 0.012,
    imb: float = 0.25,
) -> PreMarketFeatures:
    return PreMarketFeatures(
        ticker="TEST",
        prev_close=100.0,
        pre_market_vwap=100.0 * (1 + gap),
        pre_market_high=100.0 * (1 + gap) * 1.008,
        pre_market_low=100.0 * (1 + gap) * 0.992,
        pre_market_volume=int(rel_vol * 380000),
        avg_daily_volume=2_200_000,
        relative_volume=rel_vol,
        gap_pct=gap,
        bid_ask_spread_pct=spread,
        order_book_imbalance=imb,
        news_sentiment=news,
        timestamp=datetime.now(timezone.utc),
    )


async def _get_prediction(engine, feats):
    pred = engine.predict(feats)
    if hasattr(pred, "__await__"):
        pred = await pred
    return pred


def test_engine_returns_valid_prediction():
    engine = PreMarketSpeculationEngine()
    feats = make_features()
    pred = asyncio.run(_get_prediction(engine, feats))

    assert pred.predicted_direction in ("up", "down", "flat")
    assert 0.0 <= pred.volatility_score <= 1.0
    assert -1.0 <= pred.directional_score <= 1.0
    assert 0.0 <= pred.confidence <= 1.0
    assert isinstance(pred.key_drivers, list)
    assert len(pred.key_drivers) >= 1


def test_high_gap_and_volume_is_bullish():
    engine = PreMarketSpeculationEngine()
    feats = make_features(gap=0.032, rel_vol=3.7, news=0.52)
    pred = asyncio.run(_get_prediction(engine, feats))

    assert pred.predicted_direction in ("up", "flat")
    assert pred.confidence > 0.50


def test_negative_gap_and_bearish_news_is_bearish():
    engine = PreMarketSpeculationEngine()
    feats = make_features(gap=-0.028, rel_vol=2.9, news=-0.45)
    pred = asyncio.run(_get_prediction(engine, feats))

    assert pred.predicted_direction in ("down", "flat")
    assert pred.confidence > 0.45


def test_spread_expansion_increases_volatility_score():
    engine = PreMarketSpeculationEngine()
    low_spread = make_features(spread=0.006)
    high_spread = make_features(spread=0.022)

    p1 = asyncio.run(_get_prediction(engine, low_spread))
    p2 = asyncio.run(_get_prediction(engine, high_spread))

    assert p2.volatility_score >= p1.volatility_score


def test_order_book_imbalance_affects_direction():
    engine = PreMarketSpeculationEngine()
    bullish = make_features(imb=0.45)
    bearish = make_features(imb=-0.45)

    p_bull = asyncio.run(_get_prediction(engine, bullish))
    p_bear = asyncio.run(_get_prediction(engine, bearish))

    # Bullish imbalance should push direction higher than bearish
    assert p_bull.directional_score > p_bear.directional_score
