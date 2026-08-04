"""
Entry point / orchestrator for the EquityScanner engine.
Demonstrates usage of the full stack.
"""
import asyncio
from datetime import datetime

from stock_scanner.config import config
from stock_scanner.ingestion.data_ingestor import AsyncDataIngestor
from stock_scanner.processing.live_processor import LiveMarketProcessor
from stock_scanner.nlp.sentiment_engine import SentimentEngine
from stock_scanner.premarket.speculation_engine import PreMarketSpeculationEngine
from stock_scanner.reporting.report_generator import ReportGenerator


async def demo_full_stack(tickers: list[str]):
    print("=== EquityScanner Pro Demo ===")
    
    async with AsyncDataIngestor() as ingestor:
        processor = LiveMarketProcessor()
        await processor.connect()
        
        sentiment = SentimentEngine()
        premarket = PreMarketSpeculationEngine()
        
        report_gen = ReportGenerator(ingestor, processor, sentiment, premarket)
        
        # 1. Fetch some live data (simulated)
        print("\n[1] Fetching quotes...")
        quotes = await ingestor.fetch_quotes(tickers)
        for q in quotes:
            print(f"  {q.ticker}: bid={q.bid} ask={q.ask}")
        
        # 2. Simulate live processing callbacks (in prod: from WS)
        print("\n[2] Processing sample trade/quote events...")
        for tkr in tickers:
            await processor.on_trade({
                "ticker": tkr, "price": 152.75, "size": 450,
                "timestamp": datetime.utcnow(), "conditions": []
            })
            await processor.on_quote({
                "ticker": tkr, "bid": 152.70, "ask": 152.80,
                "bid_size": 1200, "ask_size": 850,
                "timestamp": datetime.utcnow()
            })
        
        # 3. Generate full report (core requirement)
        print("\n[3] Generating structured report for", tickers[0])
        report = await report_gen.generate_full_report(tickers[0], include_premarket=True)
        print("Report generated at:", report.generated_at)
        print("Summary:", report.summary_text)
        print("Recommendation:", report.recommendation)
        
        if report.premarket_prediction:
            pm = report.premarket_prediction
            print(f"\nPre-Market Prediction:")
            print(f"  Direction: {pm.predicted_direction.upper()} | Vol Score: {pm.volatility_score}")
            print(f"  Expected Move: ±{pm.expected_move_pct}% | Confidence: {pm.confidence:.0%}")
            print(f"  Drivers: {', '.join(pm.key_drivers)}")
        
        # 4. Direct pre-market prediction example
        print("\n[4] Direct pre-market speculation call...")
        features = await processor.build_pre_market_features(tickers[0], prev_close=149.20, avg_daily_vol=3200000)
        if features:
            features.news_sentiment = 0.48
            pred = await premarket.predict(features)
            print(f"  Volatility: {pred.volatility_score} | Direction: {pred.predicted_direction}")
        
        await processor.disconnect()
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    asyncio.run(demo_full_stack(["AAPL", "NVDA"]))
