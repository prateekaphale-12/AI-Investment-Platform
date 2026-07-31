"""
AI Orchestration Service

Coordinates event-triggered AI analysis:
- Listens to event queue
- Triggers existing analysis services
- Manages analysis cooldowns
- Publishes results to WebSocket clients

Philosophy:
- Don't rerun AI every second
- Only analyze on significant events
- Reuse existing analysis services
- Cache results efficiently
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from redis.asyncio import Redis
from loguru import logger


class AIOrchestrator:
    """
    Orchestrates event-triggered AI analysis.
    
    Responsibilities:
    - Process event queue
    - Trigger analysis for significant events
    - Manage analysis cooldowns
    - Publish results to clients
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[Redis] = None
        self.running = False
        
        # Analysis cooldowns (prevent spam)
        self.last_analysis: Dict[str, datetime] = {}  # ticker -> last analysis time
        self.cooldown_period = timedelta(minutes=10)  # Min time between analyses
        
        # Analysis cache
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}  # ticker -> analysis result
        self.cache_ttl = timedelta(minutes=15)
        
    async def start(self):
        """Start AI orchestrator"""
        self.running = True
        self.redis = Redis.from_url(self.redis_url, decode_responses=True)
        logger.info("AIOrchestrator started")
        
        # Start processing queue
        await self._process_event_queue()
    
    async def stop(self):
        """Stop AI orchestrator"""
        self.running = False
        if self.redis:
            await self.redis.close()
        logger.info("AIOrchestrator stopped")
    
    async def _process_event_queue(self):
        """Process events from Redis queue"""
        while self.running:
            try:
                # Block for 1 second waiting for events
                event_data = await self.redis.brpop("queue:ai_analysis", timeout=1)
                
                if event_data:
                    _, event_json = event_data
                    event = json.loads(event_json)
                    await self._handle_event(event)
                    
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")
                await asyncio.sleep(1)
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle a single event"""
        ticker = event.get("ticker")
        event_type = event.get("event_type")
        
        if not ticker or ticker == "MARKET":
            return  # Skip market-wide events for now
        
        # Check cooldown
        last_analysis = self.last_analysis.get(ticker)
        if last_analysis and (datetime.now() - last_analysis) < self.cooldown_period:
            logger.info(f"Skipping analysis for {ticker} (cooldown)")
            return
        
        logger.info(f"Triggering AI analysis for {ticker} due to {event_type}")
        
        try:
            # Run analysis
            result = await self._analyze_ticker(ticker, event)
            
            # Update cooldown
            self.last_analysis[ticker] = datetime.now()
            
            # Cache result
            self.analysis_cache[ticker] = {
                "result": result,
                "timestamp": datetime.now(),
            }
            
            # Publish to WebSocket clients
            await self._publish_analysis_result(ticker, result, event)
            
        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
    
    async def _analyze_ticker(self, ticker: str, event: Dict[str, Any]) -> Dict[str, Any]:
        """Run AI analysis for a ticker"""
        from app.services.stock_service import build_market_row
        from app.services.technical_service import analyze_technical
        from app.services.sentiment_service import analyze_sentiment
        from app.services.confidence_engine import calculate_confidence
        
        # Fetch stock data
        stock_data = await build_market_row(None, ticker)
        if "error" in stock_data:
            raise ValueError(f"No data for {ticker}: {stock_data['error']}")
        
        # Run technical analysis
        technical = await analyze_technical(ticker, stock_data)
        
        # Run sentiment analysis
        sentiment = await analyze_sentiment(ticker)
        
        # Calculate confidence
        confidence_data = calculate_confidence(
            technical=technical,
            fundamental=stock_data.get("info", {}),
            sentiment=sentiment,
        )
        
        return {
            "ticker": ticker,
            "price": stock_data.get("current_price"),
            "ytd_return": stock_data.get("ytd_return_pct"),
            "technical": technical,
            "sentiment": sentiment,
            "confidence": confidence_data,
            "event_trigger": event.get("event_type"),
            "analyzed_at": datetime.now().isoformat(),
        }
    
    async def _publish_analysis_result(
        self,
        ticker: str,
        result: Dict[str, Any],
        event: Dict[str, Any]
    ):
        """Publish analysis result to WebSocket clients"""
        if not self.redis:
            return
        
        message = {
            "type": "ai_analysis",
            "ticker": ticker,
            "result": result,
            "event": event,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Publish to Redis (WebSocket manager will broadcast)
        await self.redis.publish(
            "ai:analysis:complete",
            json.dumps(message)
        )
        
        logger.info(f"Published AI analysis for {ticker}")


# Global instance
_ai_orchestrator: Optional[AIOrchestrator] = None


async def get_ai_orchestrator() -> AIOrchestrator:
    """Get or create AI orchestrator instance"""
    global _ai_orchestrator
    if _ai_orchestrator is None:
        from app.config import settings
        _ai_orchestrator = AIOrchestrator(redis_url=settings.redis_url)
    return _ai_orchestrator
