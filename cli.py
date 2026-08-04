"""
EquityScanner Pro — Command Line Interface

Simple but powerful CLI built with Typer.

Install with: pip install -e .
Then use: equityscanner --help

Or run directly: python -m cli
"""

import typer
from rich.console import Console
from rich.table import Table
from datetime import datetime

from premarket.speculation_engine import PreMarketSpeculationEngine
from utils.models import PreMarketFeatures
from reporting.report_generator import ReportGenerator
from processing.live_processor import LiveMarketProcessor
from nlp.sentiment_engine import SentimentEngine
from ingestion.data_ingestor import AsyncDataIngestor

app = typer.Typer(help="EquityScanner Pro - Real-time stock scanner & pre-market engine")
console = Console()

@app.command()
def predict(
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g. AAPL)"),
    gap: float = typer.Option(0.015, help="Pre-market gap %"),
    rel_vol: float = typer.Option(2.3, help="Relative volume"),
    news: float = typer.Option(0.35, help="News sentiment score (-1 to +1)"),
):
    """Get pre-market prediction for a ticker (uses demo features if not live)."""
    engine = PreMarketSpeculationEngine()
    
    feat = PreMarketFeatures(
        ticker=ticker.upper(),
        prev_close=150.0,
        pre_market_vwap=150.0 * (1 + gap),
        pre_market_high=150.0 * (1 + gap) * 1.008,
        pre_market_low=150.0 * (1 + gap) * 0.992,
        pre_market_volume=int(rel_vol * 380000),
        avg_daily_volume=2_200_000,
        relative_volume=rel_vol,
        gap_pct=gap,
        bid_ask_spread_pct=0.011,
        order_book_imbalance=0.22,
        news_sentiment=news,
        timestamp=datetime.utcnow()
    )
    
    pred = engine.predict(feat)
    
    console.print(f"\n[bold]Pre-Market Prediction for {ticker.upper()}[/bold]")
    table = Table()
    table.add_column("Metric")
    table.add_column("Value")
    
    table.add_row("Direction", f"[bold]{pred.predicted_direction.upper()}[/bold]")
    table.add_row("Volatility Score", f"{pred.volatility_score:.0%}")
    table.add_row("Directional Score", f"{pred.directional_score:+.2f}")
    table.add_row("Confidence", f"{pred.confidence:.0%}")
    table.add_row("Expected Move", f"±{pred.expected_move_pct}%")
    table.add_row("Key Drivers", ", ".join(pred.key_drivers[:3]))
    
    console.print(table)

@app.command()
def report(
    ticker: str = typer.Argument(..., help="Ticker to analyze"),
    premarket: bool = typer.Option(True, help="Include pre-market prediction"),
):
    """Generate full equity report."""
    import asyncio
    
    async def _run():
        proc = LiveMarketProcessor()
        await proc.connect()
        
        # Seed some data
        from api.seed_demo import seed_demo_pre_market_data
        await seed_demo_pre_market_data(proc, ticker.upper())
        
        gen = ReportGenerator(
            AsyncDataIngestor(), 
            proc, 
            SentimentEngine(), 
            PreMarketSpeculationEngine()
        )
        r = await gen.generate_full_report(ticker.upper(), include_premarket=premarket)
        
        console.print(f"\n[bold cyan]Equity Report — {r.ticker}[/bold cyan]")
        console.print(f"Generated: {r.generated_at}")
        console.print(f"\n[bold]Recommendation:[/bold] {r.recommendation}")
        console.print(f"\nSummary: {r.summary_text}")
        
        if r.premarket_prediction:
            pm = r.premarket_prediction
            console.print(f"\n[bold]Pre-Market:[/bold] {pm.predicted_direction.upper()} (conf {pm.confidence:.0%})")
        
        await proc.disconnect()
    
    asyncio.run(_run())

@app.command()
def backtest(days: int = typer.Option(50, help="Number of simulated days")):
    """Run the pre-market backtest (old vs new logic)."""
    from dashboard.backtest import run_backtest
    
    bt = run_backtest(n_days=days)
    console.print(f"\n[bold]Backtest Results ({days} days)[/bold]")
    console.print(f"New Logic Accuracy: {bt['new_accuracy']:.1%}")
    console.print(f"Old Logic Accuracy: {bt['old_accuracy']:.1%}")
    console.print(f"Improvement: +{bt['improvement']}%")
    console.print(f"New Cumulative Return: {bt['new_cum_return_pct']:+.1f}%")

if __name__ == "__main__":
    app()
