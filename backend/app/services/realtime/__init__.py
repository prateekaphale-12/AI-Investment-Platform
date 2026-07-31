"""
Real-time Market Intelligence Services

This package provides real-time market data streaming, event detection,
and AI-powered analysis orchestration.

Components:
- StreamManager: Finnhub WebSocket connection and price streaming
- EventDetector: Market event detection and filtering
- AIOrchestrator: Event-triggered AI analysis coordination
- NewsStreamManager: Breaking news aggregation
- RealtimeServiceManager: Lifecycle management for all services

Usage:
    from app.services.realtime.launcher import start_realtime_services
    await start_realtime_services()
"""

from app.services.realtime.stream_manager import (
    StreamManager,
    NewsStreamManager,
    get_stream_manager,
    get_news_manager,
)
from app.services.realtime.event_detector import (
    EventDetector,
    MarketEvent,
    get_event_detector,
)
from app.services.realtime.ai_orchestrator import (
    AIOrchestrator,
    get_ai_orchestrator,
)
from app.services.realtime.launcher import (
    RealtimeServiceManager,
    start_realtime_services,
    stop_realtime_services,
)

__all__ = [
    "StreamManager",
    "NewsStreamManager",
    "EventDetector",
    "MarketEvent",
    "AIOrchestrator",
    "RealtimeServiceManager",
    "get_stream_manager",
    "get_news_manager",
    "get_event_detector",
    "get_ai_orchestrator",
    "start_realtime_services",
    "stop_realtime_services",
]
