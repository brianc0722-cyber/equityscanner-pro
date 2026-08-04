"""
NLP Pipeline: Sector-wide news aggregation + FinBERT sentiment.
Uses HuggingFace transformers (async compatible).
Aggregates bullish/bearish themes for sectors and tickers.

This module now gracefully degrades when transformers is not installed
(e.g. on Render free tier). It falls back to neutral sentiment.
"""

import asyncio
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import numpy as np

# === Conditional import for transformers (heavy) ===
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from config import config
from utils.models import NewsItem, SentimentResult, SectorNewsInsight


class SentimentEngine:
    def __init__(self):
        self._classifier = None
        self._tokenizer = None
        self._model = None
        self.sector_news: Dict[str, List[NewsItem]] = defaultdict(list)
        self.ticker_sentiment_cache: Dict[str, SentimentResult] = {}
        self._lock = asyncio.Lock()
        self._transformers_available = TRANSFORMERS_AVAILABLE

    async def _load_model(self):
        """Lazy load FinBERT only if transformers is available."""
        if not self._transformers_available:
            return

        if self._classifier is None:
            try:
                self._classifier = pipeline(
                    "sentiment-analysis",
                    model=config.FINBERT_MODEL,
                    tokenizer=config.FINBERT_MODEL,
                    device=-1,
                    framework="pt"
                )
                self._tokenizer = AutoTokenizer.from_pretrained(config.FINBERT_MODEL)
            except Exception as e:
                print(f"⚠️  FinBERT model load failed (falling back to neutral): {e}")
                self._transformers_available = False

    async def analyze_text(self, text: str) -> Tuple[float, str, float]:
        await self._load_model()

        if not self._transformers_available or self._classifier is None:
            return 0.0, "neutral", 0.5

        result = self._classifier(text[:512])[0]
        label = result["label"].lower()
        score = result["score"]

        if label == "positive":
            return score, "bullish", score
        elif label == "negative":
            return -score, "bearish", score
        else:
            return 0.0, "neutral", score

    async def analyze_news_batch(self, news_items: List[NewsItem]) -> Dict[str, SentimentResult]:
        await self._load_model()
        results = {}
        ticker_scores = defaultdict(list)
        ticker_sources = defaultdict(int)

        for item in news_items:
            if not item.headline and not item.body:
                continue
            text = f"{item.headline}. {item.body}"[:512]

            if self._transformers_available:
                score, label, conf = await self.analyze_text(text)
            else:
                score, label, conf = 0.0, "neutral", 0.5

            ticker_scores[item.ticker].append(score)
            ticker_sources[item.ticker] += 1
            if item.sector:
                self.sector_news[item.sector].append(item)

        for ticker, scores in ticker_scores.items():
            avg_score = float(np.mean(scores))
            avg_conf = float(np.mean([abs(s) for s in scores]))
            label = "bullish" if avg_score > 0.15 else "bearish" if avg_score < -0.15 else "neutral"

            res = SentimentResult(
                ticker=ticker,
                score=round(avg_score, 4),
                label=label,
                confidence=round(avg_conf, 3),
                source_count=ticker_sources[ticker],
                timestamp=datetime.utcnow()
            )
            results[ticker] = res
            self.ticker_sentiment_cache[ticker] = res

        return results

    async def get_sector_insights(self, sector: str) -> SectorNewsInsight:
        items = [i for i in self.sector_news[sector] 
                 if (datetime.utcnow() - i.published_at).total_seconds() < config.SECTOR_NEWS_WINDOW_MINUTES * 60]

        if not items:
            return SectorNewsInsight(
                sector=sector, aggregate_sentiment=0.0,
                bullish_themes=[], bearish_themes=[],
                top_headlines=[], news_count=0, timestamp=datetime.utcnow()
            )

        scores = []
        headlines = []
        for item in items[:25]:
            if self._transformers_available:
                score, _, _ = await self.analyze_text(item.headline)
            else:
                score = 0.0
            scores.append(score)
            headlines.append(item.headline)

        agg_sent = float(np.mean(scores)) if scores else 0.0

        bullish = []
        bearish = []
        for item in items:
            if self._transformers_available:
                s, label, _ = await self.analyze_text(item.headline)
            else:
                s, label = 0.0, "neutral"
            if label == "bullish" and len(bullish) < 5:
                bullish.append(item.headline[:80])
            elif label == "bearish" and len(bearish) < 5:
                bearish.append(item.headline[:80])

        return SectorNewsInsight(
            sector=sector,
            aggregate_sentiment=round(agg_sent, 4),
            bullish_themes=bullish,
            bearish_themes=bearish,
            top_headlines=headlines[:5],
            news_count=len(items),
            timestamp=datetime.utcnow()
        )

    async def get_ticker_sentiment(self, ticker: str) -> SentimentResult:
        if ticker in self.ticker_sentiment_cache:
            return self.ticker_sentiment_cache[ticker]
        return SentimentResult(ticker=ticker, score=0.0, label="neutral", confidence=0.5, source_count=0, timestamp=datetime.utcnow())
