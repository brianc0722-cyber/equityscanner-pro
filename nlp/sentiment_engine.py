"""
NLP Pipeline: Sector-wide news aggregation + FinBERT sentiment.
Uses HuggingFace transformers (async compatible).
Aggregates bullish/bearish themes for sectors and tickers.
"""
import asyncio
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import numpy as np
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

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

    async def _load_model(self):
        """Lazy load FinBERT."""
        if self._classifier is None:
            # FinBERT is a financial domain specific BERT fine-tuned on financial sentiment
            self._classifier = pipeline(
                "sentiment-analysis",
                model=config.FINBERT_MODEL,
                tokenizer=config.FINBERT_MODEL,
                device=-1,  # CPU; use 0 for GPU in prod
                framework="pt"
            )
            self._tokenizer = AutoTokenizer.from_pretrained(config.FINBERT_MODEL)

    async def analyze_text(self, text: str) -> Tuple[float, str, float]:
        """Single text sentiment using FinBERT. Returns score, label, confidence."""
        await self._load_model()
        
        # FinBERT labels: positive, negative, neutral
        result = self._classifier(text[:512])[0]  # truncate
        label = result["label"].lower()
        score = result["score"]
        
        # Map to -1 to +1 continuous score
        if label == "positive":
            mapped_score = score
            mapped_label = "bullish"
        elif label == "negative":
            mapped_score = -score
            mapped_label = "bearish"
        else:
            mapped_score = 0.0
            mapped_label = "neutral"
        
        return mapped_score, mapped_label, score

    async def analyze_news_batch(self, news_items: List[NewsItem]) -> Dict[str, SentimentResult]:
        """Batch sentiment on news. Returns ticker -> SentimentResult."""
        await self._load_model()
        
        results = {}
        ticker_scores = defaultdict(list)
        ticker_sources = defaultdict(int)
        
        for item in news_items:
            if not item.headline and not item.body:
                continue
            text = f"{item.headline}. {item.body}"[:512]
            score, label, conf = await self.analyze_text(text)
            
            ticker_scores[item.ticker].append(score)
            ticker_sources[item.ticker] += 1
            
            # Store sector news
            if item.sector:
                self.sector_news[item.sector].append(item)
        
        for ticker, scores in ticker_scores.items():
            avg_score = float(np.mean(scores))
            avg_conf = float(np.mean([abs(s) for s in scores]))  # rough
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
        """Aggregate sector themes."""
        items = [i for i in self.sector_news[sector] 
                 if (datetime.utcnow() - i.published_at).total_seconds() < config.SECTOR_NEWS_WINDOW_MINUTES * 60]
        
        if not items:
            return SectorNewsInsight(
                sector=sector, aggregate_sentiment=0.0,
                bullish_themes=[], bearish_themes=[],
                top_headlines=[], news_count=0, timestamp=datetime.utcnow()
            )
        
        # Analyze all headlines
        scores = []
        headlines = []
        for item in items[:25]:
            score, _, _ = await self.analyze_text(item.headline)
            scores.append(score)
            headlines.append(item.headline)
        
        agg_sent = float(np.mean(scores)) if scores else 0.0
        
        # Naive theme extraction (in production use topic modeling / LLM)
        bullish = []
        bearish = []
        for item in items:
            s, label, _ = await self.analyze_text(item.headline)
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
