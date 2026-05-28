"""
Event Detection Layer

Monitors real-time data streams and detects significant events that warrant AI analysis:
- Price threshold breaches (>2% move)
- Volume spikes (>3x average)
- Sentiment shifts (major change in news tone)
- Breaking news (earnings, M&A, regulatory)
- Portfolio drift (allocation deviation >5%)

Philosophy:
- AI analysis is expensive, run it only when needed
- Use deterministic rules for event detection
- Maintain event history to avoid duplicate triggers
- Calibrate thresholds based on volatility
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from collections import deque
from dataclasses import dataclass

from redis.asyncio import Redis
from loguru import logger


@dataclass
class MarketEvent:
    """Represents a significant market event"""
    event_type: str  # price_move, volume_spike, sentiment_shift, breaking_news
    ticker: str
    severity: str  # low, medium, high, critical
    data: Dict[str, Any]
    timestamp: datetime
    requires_ai_analysis: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "ticker": self.ticker,
            "severity": self.severity,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "requires_ai_analysis": self.requires_ai_analysis,
        }


class EventDetector:
    """
    Detects significant market events from real-time data streams.
    
    Responsibilities:
    - Monitor price movements
    - Detect volume anomalies
    - Track sentiment changes
    - Filter breaking news
    - Trigger AI analysis when needed
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.running = False
        
        # Price monitoring
        self.price_history: Dict[str, deque] = {}  # ticker -> deque of (timestamp, price)
        self.baseline_prices: Dict[str, float] = {}  # ticker -> baseline price
        
        # Volume monitoring
        self.volume_history: Dict[str, deque] = {}  # ticker -> deque of volumes
        self.avg_volume: Dict[str, float] = {}  # ticker -> average volume
        
        # Event deduplication
        self.recent_events: deque = deque(maxlen=1000)
        self.event_cooldown: Dict[str, datetime] = {}  # event_key -> last trigger time
        
        # Thresholds
        self.price_move_threshold = 0.02  # 2% move triggers event
        self.volume_spike_threshold = 3.0  # 3x average volume
        self.cooldown_period = timedelta(minutes=15)  # Min time between same events
        
    async def start(self):
        """Start event detector"""
        self.running = True
        self.redis = Redis.from_url(self.redis_url, decode_responses=True)
        logger.info("EventDetector started")
        
        # Subscribe to Redis channels
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(
            "market:price:all",
            "market:news:breaking",
            "market:aggregate:*",
        )
        
        # Start monitoring
        await asyncio.gather(
            self._monitor_redis_stream(pubsub),
            self._periodic_analysis(),
        )
    
    async def stop(self):
        """Stop event detector"""
        self.running = False
        if self.redis:
            await self.redis.close()
        logger.info("EventDetector stopped")
    
    async def _monitor_redis_stream(self, pubsub):
        """Monitor Redis pub/sub for real-time updates"""
        while self.running:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message:
                    await self._handle_redis_message(message)
            except Exception as e:
                logger.error(f"Error monitoring Redis stream: {e}")
                await asyncio.sleep(1)
    
    async def _handle_redis_message(self, message: Dict[str, Any]):
        """Handle incoming Redis message"""
        import json
        
        channel = message.get("channel", "")
        data_str = message.get("data", "")
        
        if not data_str or not isinstance(data_str, str):
            return
        
        try:
            data = json.loads(data_str)
            
            if "price" in channel:
                await self._check_price_event(data)
            elif "news" in channel:
                await self._check_news_event(data)
            elif "aggregate" in channel:
                await self._check_volume_event(data)
                
        except json.JSONDecodeError:
            logger.error(f"Failed to decode Redis message: {data_str}")
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")
    
    async def _check_price_event(self, data: Dict[str, Any]):
        """Check if price update triggers an event"""
        ticker = data.get("ticker")
        price = data.get("price")
        timestamp = data.get("timestamp")
        
        if not ticker or not price:
            return
        
        # Initialize history if needed
        if ticker not in self.price_history:
            self.price_history[ticker] = deque(maxlen=100)
            self.baseline_prices[ticker] = price
        
        # Add to history
        self.price_history[ticker].append((timestamp, price))
        
        # Check for significant move
        baseline = self.baseline_prices[ticker]
        pct_change = (price - baseline) / baseline
        
        if abs(pct_change) >= self.price_move_threshold:
            event = MarketEvent(
                event_type="price_move",
                ticker=ticker,
                severity=self._calculate_severity(abs(pct_change)),
                data={
                    "price": price,
                    "baseline": baseline,
                    "pct_change": pct_change,
                    "direction": "up" if pct_change > 0 else "down",
                },
                timestamp=datetime.now(),
                requires_ai_analysis=abs(pct_change) >= 0.05,  # 5% move requires AI
            )
            
            await self._emit_event(event)
            
            # Update baseline after significant move
            self.baseline_prices[ticker] = price
    
    async def _check_volume_event(self, data: Dict[str, Any]):
        """Check if volume triggers an event"""
        ticker = data.get("ticker")
        total_volume = data.get("total_volume")
        
        if not ticker or not total_volume:
            return
        
        # Initialize history if needed
        if ticker not in self.volume_history:
            self.volume_history[ticker] = deque(maxlen=50)
            self.avg_volume[ticker] = total_volume
        
        # Add to history
        self.volume_history[ticker].append(total_volume)
        
        # Calculate average
        if len(self.volume_history[ticker]) >= 10:
            self.avg_volume[ticker] = sum(self.volume_history[ticker]) / len(self.volume_history[ticker])
        
        # Check for spike
        avg = self.avg_volume[ticker]
        if total_volume > avg * self.volume_spike_threshold:
            event = MarketEvent(
                event_type="volume_spike",
                ticker=ticker,
                severity="medium",
                data={
                    "volume": total_volume,
                    "avg_volume": avg,
                    "spike_ratio": total_volume / avg,
                },
                timestamp=datetime.now(),
                requires_ai_analysis=total_volume > avg * 5.0,  # 5x spike requires AI
            )
            
            await self._emit_event(event)
    
    async def _check_news_event(self, data: Dict[str, Any]):
        """Check if news article triggers an event"""
        article = data.get("article", {})
        title = article.get("title", "").lower()
        
        # Keywords that trigger AI analysis
        critical_keywords = [
            "earnings", "acquisition", "merger", "bankruptcy", "sec", "fda",
            "recall", "lawsuit", "investigation", "ceo", "guidance", "forecast"
        ]
        
        is_critical = any(keyword in title for keyword in critical_keywords)
        
        if is_critical:
            event = MarketEvent(
                event_type="breaking_news",
                ticker="MARKET",  # Could extract ticker from article
                severity="high" if is_critical else "medium",
                data={
                    "title": article.get("title"),
                    "source": article.get("source"),
                    "url": article.get("url"),
                },
                timestamp=datetime.now(),
                requires_ai_analysis=is_critical,
            )
            
            await self._emit_event(event)
    
    async def _emit_event(self, event: MarketEvent):
        """Emit event to Redis and check for AI trigger"""
        # Check cooldown
        event_key = f"{event.event_type}:{event.ticker}"
        last_trigger = self.event_cooldown.get(event_key)
        
        if last_trigger and (datetime.now() - last_trigger) < self.cooldown_period:
            return  # Skip, too soon
        
        # Update cooldown
        self.event_cooldown[event_key] = datetime.now()
        
        # Add to recent events
        self.recent_events.append(event)
        
        # Publish to Redis
        if self.redis:
            import json
            await self.redis.publish(
                f"events:{event.event_type}",
                json.dumps(event.to_dict())
            )
            
            # If requires AI analysis, publish to AI queue
            if event.requires_ai_analysis:
                await self.redis.lpush(
                    "queue:ai_analysis",
                    json.dumps(event.to_dict())
                )
                logger.info(f"Triggered AI analysis for {event.ticker}: {event.event_type}")
        
        logger.info(f"Event detected: {event.event_type} for {event.ticker} (severity: {event.severity})")
    
    def _calculate_severity(self, pct_change: float) -> str:
        """Calculate event severity based on magnitude"""
        if pct_change >= 0.10:  # 10%+
            return "critical"
        elif pct_change >= 0.05:  # 5-10%
            return "high"
        elif pct_change >= 0.03:  # 3-5%
            return "medium"
        else:
            return "low"
    
    async def _periodic_analysis(self):
        """Periodically analyze market conditions"""
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes
            
            try:
                # Calculate market-wide metrics
                if self.price_history:
                    total_tickers = len(self.price_history)
                    gainers = sum(
                        1 for ticker, history in self.price_history.items()
                        if history and history[-1][1] > self.baseline_prices.get(ticker, 0)
                    )
                    
                    market_breadth = gainers / total_tickers if total_tickers > 0 else 0.5
                    
                    # Publish market health metric
                    if self.redis:
                        import json
                        await self.redis.publish(
                            "market:health",
                            json.dumps({
                                "market_breadth": market_breadth,
                                "total_tickers": total_tickers,
                                "gainers": gainers,
                                "losers": total_tickers - gainers,
                                "timestamp": datetime.now().isoformat(),
                            })
                        )
                        
            except Exception as e:
                logger.error(f"Error in periodic analysis: {e}")


# Global instance
_event_detector: Optional[EventDetector] = None


async def get_event_detector() -> EventDetector:
    """Get or create event detector instance"""
    global _event_detector
    if _event_detector is None:
        from app.config import settings
        _event_detector = EventDetector(redis_url=settings.redis_url)
    return _event_detector
