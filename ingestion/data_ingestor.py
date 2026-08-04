"""
Core asynchronous data ingestion layer.
Handles REST + WebSocket streams from multiple providers (Alpaca, Polygon, Finnhub).
Uses asyncio, aiohttp, websockets.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import AsyncGenerator, Dict, List, Optional, Callable

import aiohttp
import websockets
from aiokafka import AIOKafkaProducer

from config import config
from utils.models import Quote, Trade, Bar, NewsItem

class AsyncDataIngestor:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.kafka_producer: Optional[AIOKafkaProducer] = None
        self._running = False
        self.callbacks: Dict[str, List[Callable]] = {
            "trade": [], "quote": [], "bar": [], "news": []
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "EquityScanner/1.0"}
        )
        # Kafka is optional — only connect if explicitly wanted and available
        if config.KAFKA_BOOTSTRAP_SERVERS and config.KAFKA_BOOTSTRAP_SERVERS != "localhost:9092":
            try:
                self.kafka_producer = AIOKafkaProducer(
                    bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8")
                )
                await self.kafka_producer.start()
                print("Kafka producer connected")
            except Exception as e:
                print(f"Kafka not available (demo mode): {e}")
                self.kafka_producer = None
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()
        if self.session:
            await self.session.close()
        if self.kafka_producer:
            await self.kafka_producer.stop()

    def register_callback(self, event_type: str, callback: Callable):
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)

    async def _publish(self, topic: str, data: dict):
        """Publish to Kafka or in-memory for decoupling."""
        if self.kafka_producer:
            await self.kafka_producer.send_and_wait(topic, data)
        # Also invoke callbacks
        for cb in self.callbacks.get(topic.split("_")[0], []):
            try:
                await cb(data)
            except Exception:
                pass

    # === REST APIs ===
    async def fetch_quotes(self, tickers: List[str]) -> List[Quote]:
        """Fetch latest quotes via Alpaca or Polygon REST."""
        if not self.session:
            raise RuntimeError("Ingestor not initialized")
        
        headers = {"APCA-API-KEY-ID": config.ALPACA_API_KEY, "APCA-API-SECRET-KEY": config.ALPACA_API_SECRET}
        url = "https://data.alpaca.markets/v2/stocks/quotes/latest"
        
        params = {"symbols": ",".join(tickers)}
        async with self.session.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                resp.raise_for_status()
            data = await resp.json()
        
        quotes = []
        for ticker, q in data.get("quotes", {}).items():
            quotes.append(Quote(
                ticker=ticker,
                bid=q.get("bp", 0.0),
                ask=q.get("ap", 0.0),
                bid_size=q.get("bs", 0),
                ask_size=q.get("as", 0),
                timestamp=datetime.fromisoformat(q["t"].replace("Z", "+00:00")),
                exchange=q.get("x")
            ))
        return quotes

    async def fetch_bars(self, ticker: str, start: datetime, end: datetime, interval: str = "1Min") -> List[Bar]:
        """Historical bars (used for VWAP, rel volume)."""
        if not self.session:
            raise RuntimeError("Ingestor not initialized")

        headers = {"APCA-API-KEY-ID": config.ALPACA_API_KEY, "APCA-API-SECRET-KEY": config.ALPACA_API_SECRET}
        url = f"https://data.alpaca.markets/v2/stocks/{ticker}/bars"
        
        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timeframe": interval,
            "limit": 10000
        }
        async with self.session.get(url, headers=headers, params=params) as resp:
            data = await resp.json()
        
        bars = []
        for b in data.get("bars", []):
            bars.append(Bar(
                ticker=ticker,
                open=b["o"], high=b["h"], low=b["l"], close=b["c"],
                volume=b["v"], vwap=b.get("vw", b["c"]),
                timestamp=datetime.fromisoformat(b["t"].replace("Z", "+00:00")),
                interval=interval
            ))
        return bars

    async def fetch_fundamentals(self, ticker: str) -> Dict:
        """Fundamentals via FMP or Polygon."""
        if not self.session or not config.FMP_API_KEY:
            return {}
        url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}"
        async with self.session.get(url, params={"apikey": config.FMP_API_KEY}) as resp:
            data = await resp.json()
            return data[0] if data else {}

    async def fetch_news(self, tickers: Optional[List[str]] = None, limit: int = 50) -> List[NewsItem]:
        """News via Finnhub or Alpaca."""
        if not self.session:
            return []
        
        headers = {"X-Finnhub-Token": config.FINNHUB_API_KEY}
        url = "https://finnhub.io/api/v1/news"
        params = {"category": "general", "minId": 0}
        if tickers:
            params["symbol"] = tickers[0]  # Finnhub supports single symbol or general
        
        async with self.session.get(url, headers=headers, params=params) as resp:
            items = await resp.json()
        
        news = []
        for item in items[:limit]:
            news.append(NewsItem(
                ticker=item.get("related", [""])[0] if isinstance(item.get("related"), list) else tickers[0] if tickers else "",
                headline=item.get("headline", ""),
                body=item.get("summary", ""),
                published_at=datetime.fromtimestamp(item.get("datetime", 0)),
                source=item.get("source", "finnhub"),
                url=item.get("url"),
                sector=item.get("category")
            ))
        return news

    # === Real-time WebSocket Streams ===
    async def start_alpaca_stream(self, tickers: List[str]):
        """Alpaca WebSocket for trades + quotes (real-time)."""
        uri = "wss://stream.data.alpaca.markets/v2/iex"
        headers = {"APCA-API-KEY-ID": config.ALPACA_API_KEY, "APCA-API-SECRET-KEY": config.ALPACA_API_SECRET}
        
        async with websockets.connect(uri, extra_headers=headers) as ws:
            self.ws_connections["alpaca"] = ws
            auth_msg = {"action": "auth", "key": config.ALPACA_API_KEY, "secret": config.ALPACA_API_SECRET}
            await ws.send(json.dumps(auth_msg))
            
            # Subscribe
            sub_msg = {"action": "subscribe", "trades": tickers, "quotes": tickers}
            await ws.send(json.dumps(sub_msg))
            
            async for message in ws:
                data = json.loads(message)
                if data.get("T") == "t":  # trade
                    trade = Trade(
                        ticker=data["S"],
                        price=data["p"],
                        size=data["s"],
                        timestamp=datetime.fromisoformat(data["t"].replace("Z", "+00:00")),
                        conditions=data.get("c", [])
                    )
                    await self._publish("trade", trade.__dict__)
                elif data.get("T") == "q":
                    quote = Quote(
                        ticker=data["S"],
                        bid=data["bp"],
                        ask=data["ap"],
                        bid_size=data["bs"],
                        ask_size=data["as"],
                        timestamp=datetime.fromisoformat(data["t"].replace("Z", "+00:00"))
                    )
                    await self._publish("quote", quote.__dict__)

    async def start_polygon_stream(self, tickers: List[str]):
        """Polygon.io WebSocket for high-fidelity tick data."""
        uri = f"wss://socket.polygon.io/stocks"
        async with websockets.connect(uri) as ws:
            self.ws_connections["polygon"] = ws
            await ws.send(json.dumps({"action": "auth", "params": config.POLYGON_API_KEY}))
            await ws.send(json.dumps({"action": "subscribe", "params": f"T.{','.join(tickers)},Q.{','.join(tickers)}"}))
            
            async for message in ws:
                data = json.loads(message)
                if data.get("ev") == "T":
                    trade = Trade(ticker=data["sym"], price=data["p"], size=data["s"], 
                                  timestamp=datetime.fromtimestamp(data["t"] / 1000))
                    await self._publish("trade", trade.__dict__)
                # Add quote handling similarly

    async def start_news_stream(self):
        """Finnhub news websocket or polling fallback."""
        # Finnhub does not offer WS for general news; use REST polling + publish
        # For demo/production: run a background task polling
        while self._running:
            try:
                news_items = await self.fetch_news(limit=10)
                for item in news_items:
                    await self._publish("news", item.__dict__)
            except Exception:
                pass
            await asyncio.sleep(45)  # Respect rate limits

    async def run_streams(self, tickers: List[str]):
        """Launch all real-time streams concurrently."""
        self._running = True
        tasks = [
            asyncio.create_task(self.start_alpaca_stream(tickers)),
            asyncio.create_task(self.start_polygon_stream(tickers)),
            asyncio.create_task(self.start_news_stream()),
        ]
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False

    async def stop(self):
        self._running = False
        for conn in list(self.ws_connections.values()):
            if conn and not conn.closed:
                await conn.close()
        self.ws_connections.clear()
