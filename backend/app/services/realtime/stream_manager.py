"""
Real-time Market Data Stream Manager

Orchestrates live data ingestion from multiple sources:
- Finnhub WebSocket for live prices
- NewsAPI for breaking headlines
- Event detection and filtering
- Redis pub/sub for distribution

Architecture:
- Async streaming with backpressure handling
- Rate limit management
- Connection resilience
- Memory-efficient buffering
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from collections import deque

from redis.asyncio import Redis
import websockets
from loguru import logger

from app.config import settings


class StreamManager:
    """
    Manages real-time data streams from multiple sources.
    
    Responsibilities:
    - Connect to Finnhub WebSocket
    - Subscribe to ticker price updates
    - Filter and normalize data
    - Publish to Redis for distribution
    - Handle reconnection and errors
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.finnhub_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribed_tickers: Set[str] = set()
        self.running = False
        
        # Rate limiting
        self.price_buffer: Dict[str, deque] = {}  # ticker -> deque of (timestamp, price)
        self.last_publish: Dict[str, float] = {}  # ticker -> last publish timestamp
        self.publish_interval = 1.0  # Minimum seconds between publishes per ticker
        
        # Connection health
        self.last_heartbeat = datetime.now()
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60
        
    async def start(self):
        """Start the stream manager"""
        self.running = True
        self.redis = Redis.from_url(self.redis_url, decode_responses=True)
        logger.info("StreamManager started")
        
        # Start background tasks
        await asyncio.gather(
            self._connect_finnhub(),
            self._health_monitor(),
            self._publish_buffered_updates(),
        )
    
    async def stop(self):
        """Stop the stream manager"""
        self.running = False
        if self.finnhub_ws:
            await self.finnhub_ws.close()
        if self.redis:
            await self.redis.close()
        logger.info("StreamManager stopped")
    
    async def subscribe_ticker(self, ticker: str):
        """Subscribe to real-time updates for a ticker"""
        if ticker in self.subscribed_tickers:
            return
        
        self.subscribed_tickers.add(ticker)
        self.price_buffer[ticker] = deque(maxlen=100)
        
        if self.finnhub_ws and self.finnhub_ws.open:
            await self._send_subscribe(ticker)
        
        logger.info(f"Subscribed to {ticker}")
    
    async def unsubscribe_ticker(self, ticker: str):
        """Unsubscribe from ticker updates"""
        if ticker not in self.subscribed_tickers:
            return
        
        self.subscribed_tickers.remove(ticker)
        if ticker in self.price_buffer:
            del self.price_buffer[ticker]
        if ticker in self.last_publish:
            del self.last_publish[ticker]
        
        if self.finnhub_ws and self.finnhub_ws.open:
            await self._send_unsubscribe(ticker)
        
        logger.info(f"Unsubscribed from {ticker}")
    
    async def _connect_finnhub(self):
        """Connect to Finnhub WebSocket and handle messages"""
        finnhub_key = settings.finnhub_api_key
        if not finnhub_key:
            logger.warning("Finnhub API key not configured, skipping WebSocket")
            return
        
        url = f"wss://ws.finnhub.io?token={finnhub_key}"
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    self.finnhub_ws = ws
                    logger.info("Connected to Finnhub WebSocket")
                    
                    # Resubscribe to all tickers
                    for ticker in self.subscribed_tickers:
                        await self._send_subscribe(ticker)
                    
                    # Listen for messages
                    async for message in ws:
                        await self._handle_finnhub_message(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Finnhub WebSocket connection closed, reconnecting...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            except Exception as e:
                logger.error(f"Finnhub WebSocket error: {e}")
                await asyncio.sleep(self.reconnect_delay)
    
    async def _send_subscribe(self, ticker: str):
        """Send subscribe message to Finnhub"""
        if self.finnhub_ws and self.finnhub_ws.open:
            await self.finnhub_ws.send(json.dumps({"type": "subscribe", "symbol": ticker}))
    
    async def _send_unsubscribe(self, ticker: str):
        """Send unsubscribe message to Finnhub"""
        if self.finnhub_ws and self.finnhub_ws.open:
            await self.finnhub_ws.send(json.dumps({"type": "unsubscribe", "symbol": ticker}))
    
    async def _handle_finnhub_message(self, message: str):
        """Handle incoming Finnhub WebSocket message"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "ping":
                self.last_heartbeat = datetime.now()
                return
            
            if data.get("type") == "trade":
                # Process trade data
                for trade in data.get("data", []):
                    ticker = trade.get("s")
                    price = trade.get("p")
                    volume = trade.get("v")
                    timestamp = trade.get("t")
                    
                    if ticker and price:
                        await self._buffer_price_update(ticker, price, volume, timestamp)
                        
        except json.JSONDecodeError:
            logger.error(f"Failed to decode Finnhub message: {message}")
        except Exception as e:
            logger.error(f"Error handling Finnhub message: {e}")
    
    async def _buffer_price_update(self, ticker: str, price: float, volume: float, timestamp: int):
        """Buffer price update with rate limiting"""
        now = datetime.now().timestamp()
        
        # Add to buffer
        if ticker in self.price_buffer:
            self.price_buffer[ticker].append((timestamp, price, volume))
        
        # Check if we should publish
        last_pub = self.last_publish.get(ticker, 0)
        if now - last_pub >= self.publish_interval:
            await self._publish_price_update(ticker, price, volume, timestamp)
            self.last_publish[ticker] = now
    
    async def _publish_price_update(self, ticker: str, price: float, volume: float, timestamp: int):
        """Publish price update to Redis"""
        if not self.redis:
            return
        
        update = {
            "type": "price",
            "ticker": ticker,
            "price": price,
            "volume": volume,
            "timestamp": timestamp,
            "server_time": datetime.now().isoformat(),
        }
        
        # Publish to Redis channel
        await self.redis.publish(f"market:price:{ticker}", json.dumps(update))
        await self.redis.publish("market:price:all", json.dumps(update))
        
        # Store latest price in Redis
        await self.redis.setex(
            f"price:latest:{ticker}",
            300,  # 5 minute TTL
            json.dumps({"price": price, "timestamp": timestamp})
        )
    
    async def _publish_buffered_updates(self):
        """Periodically publish aggregated updates from buffer"""
        while self.running:
            await asyncio.sleep(5)  # Every 5 seconds
            
            for ticker, buffer in self.price_buffer.items():
                if len(buffer) == 0:
                    continue
                
                # Calculate aggregated metrics
                prices = [p[1] for p in buffer]
                volumes = [p[2] for p in buffer]
                
                if prices:
                    agg_update = {
                        "type": "price_aggregate",
                        "ticker": ticker,
                        "high": max(prices),
                        "low": min(prices),
                        "avg": sum(prices) / len(prices),
                        "total_volume": sum(volumes),
                        "trade_count": len(buffer),
                        "timestamp": datetime.now().isoformat(),
                    }
                    
                    if self.redis:
                        await self.redis.publish(
                            f"market:aggregate:{ticker}",
                            json.dumps(agg_update)
                        )
    
    async def _health_monitor(self):
        """Monitor connection health and trigger reconnects"""
        while self.running:
            await asyncio.sleep(30)
            
            # Check heartbeat
            if (datetime.now() - self.last_heartbeat).seconds > 60:
                logger.warning("No heartbeat from Finnhub, connection may be stale")
                if self.finnhub_ws:
                    await self.finnhub_ws.close()
            
            # Log stats
            logger.info(
                f"StreamManager health: "
                f"{len(self.subscribed_tickers)} subscriptions, "
                f"buffer sizes: {sum(len(b) for b in self.price_buffer.values())}"
            )


class NewsStreamManager:
    """
    Manages real-time news stream.
    
    Responsibilities:
    - Poll NewsAPI for breaking headlines
    - Filter relevant financial news
    - Detect sentiment shifts
    - Publish to Redis
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.running = False
        self.seen_articles: Set[str] = set()
        self.poll_interval = 60  # Poll every 60 seconds
        
    async def start(self):
        """Start news stream manager"""
        self.running = True
        self.redis = Redis.from_url(self.redis_url, decode_responses=True)
        logger.info("NewsStreamManager started")
        
        await self._poll_news_loop()
    
    async def stop(self):
        """Stop news stream manager"""
        self.running = False
        if self.redis:
            await self.redis.close()
        logger.info("NewsStreamManager stopped")
    
    async def _poll_news_loop(self):
        """Poll for new headlines"""
        while self.running:
            try:
                await self._fetch_and_publish_news()
            except Exception as e:
                logger.error(f"Error polling news: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    async def _fetch_and_publish_news(self):
        """Fetch latest news and publish new articles"""
        from app.services.news_aggregator_service import get_news_aggregator
        
        news_agg = get_news_aggregator()
        
        # Fetch latest market news
        articles = await news_agg.get_market_news(limit=20, category="general")
        
        new_count = 0
        for article in articles:
            article_id = article.get("url", "")
            
            if article_id and article_id not in self.seen_articles:
                self.seen_articles.add(article_id)
                
                # Publish to Redis
                if self.redis:
                    await self.redis.publish(
                        "market:news:breaking",
                        json.dumps({
                            "type": "news",
                            "article": article,
                            "timestamp": datetime.now().isoformat(),
                        })
                    )
                
                new_count += 1
        
        if new_count > 0:
            logger.info(f"Published {new_count} new articles")
        
        # Cleanup old seen articles (keep last 1000)
        if len(self.seen_articles) > 1000:
            self.seen_articles = set(list(self.seen_articles)[-1000:])


# Global instances
_stream_manager: Optional[StreamManager] = None
_news_manager: Optional[NewsStreamManager] = None


async def get_stream_manager() -> StreamManager:
    """Get or create stream manager instance"""
    global _stream_manager
    if _stream_manager is None:
        from app.config import settings
        _stream_manager = StreamManager(redis_url=settings.redis_url)
    return _stream_manager


async def get_news_manager() -> NewsStreamManager:
    """Get or create news manager instance"""
    global _news_manager
    if _news_manager is None:
        from app.config import settings
        _news_manager = NewsStreamManager(redis_url=settings.redis_url)
    return _news_manager
