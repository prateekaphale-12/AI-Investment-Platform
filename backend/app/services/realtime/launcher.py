"""
Real-time Services Launcher

Starts and manages all real-time services:
- StreamManager (Finnhub WebSocket)
- EventDetector (Event monitoring)
- AIOrchestrator (Event-triggered analysis)
- NewsStreamManager (Breaking news)

Usage:
    from app.services.realtime.launcher import start_realtime_services
    await start_realtime_services()
"""

from __future__ import annotations

import asyncio
from typing import List, Optional

from loguru import logger

from app.services.realtime.stream_manager import get_stream_manager, get_news_manager
from app.services.realtime.event_detector import get_event_detector
from app.services.realtime.ai_orchestrator import get_ai_orchestrator


class RealtimeServiceManager:
    """Manages lifecycle of all real-time services"""
    
    def __init__(self):
        self.services: List[asyncio.Task] = []
        self.running = False
        
    async def start(self):
        """Start all real-time services"""
        if self.running:
            logger.warning("Real-time services already running")
            return
        
        self.running = True
        logger.info("Starting real-time services...")
        
        try:
            # Get service instances
            stream_manager = await get_stream_manager()
            event_detector = await get_event_detector()
            ai_orchestrator = await get_ai_orchestrator()
            news_manager = await get_news_manager()
            
            # Start services as background tasks
            self.services = [
                asyncio.create_task(stream_manager.start(), name="StreamManager"),
                asyncio.create_task(event_detector.start(), name="EventDetector"),
                asyncio.create_task(ai_orchestrator.start(), name="AIOrchestrator"),
                asyncio.create_task(news_manager.start(), name="NewsStreamManager"),
            ]
            
            logger.info(f"Started {len(self.services)} real-time services")
            
            # Wait for all services
            await asyncio.gather(*self.services, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error starting real-time services: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop all real-time services"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping real-time services...")
        
        # Cancel all tasks
        for task in self.services:
            if not task.done():
                task.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self.services, return_exceptions=True)
        
        self.services.clear()
        logger.info("Real-time services stopped")


# Global manager
_service_manager: Optional[RealtimeServiceManager] = None


async def start_realtime_services():
    """Start all real-time services"""
    global _service_manager
    if _service_manager is None:
        _service_manager = RealtimeServiceManager()
    await _service_manager.start()


async def stop_realtime_services():
    """Stop all real-time services"""
    global _service_manager
    if _service_manager:
        await _service_manager.stop()
