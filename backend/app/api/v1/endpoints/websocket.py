"""
WebSocket API Endpoint

Provides real-time data streaming to frontend clients:
- Live price updates
- Market events
- Breaking news
- Portfolio updates
- AI analysis results

Architecture:
- One WebSocket connection per client
- Subscribe to specific data channels
- Efficient message batching
- Automatic reconnection handling
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from redis.asyncio import Redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.config import settings


router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections and message distribution.
    
    Responsibilities:
    - Track active connections
    - Subscribe to Redis channels
    - Broadcast messages to clients
    - Handle client subscriptions
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # client_id -> websocket
        self.client_subscriptions: Dict[str, Set[str]] = {}  # client_id -> set of channels
        self.redis: Optional[Redis] = None
        self.pubsub_task: Optional[asyncio.Task] = None
        
    async def connect(self, client_id: str, websocket: WebSocket):
        """Register new client connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        
        # Start Redis pubsub if not already running
        if self.redis is None:
            self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
            self.pubsub_task = asyncio.create_task(self._redis_listener())
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove client connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, client_id: str, channels: List[str]):
        """Subscribe client to specific channels"""
        if client_id not in self.client_subscriptions:
            return
        
        for channel in channels:
            self.client_subscriptions[client_id].add(channel)
        
        logger.info(f"Client {client_id} subscribed to {channels}")
    
    async def unsubscribe(self, client_id: str, channels: List[str]):
        """Unsubscribe client from channels"""
        if client_id not in self.client_subscriptions:
            return
        
        for channel in channels:
            self.client_subscriptions[client_id].discard(channel)
        
        logger.info(f"Client {client_id} unsubscribed from {channels}")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any], channel: str = "all"):
        """Broadcast message to all subscribed clients"""
        disconnected = []
        
        for client_id, websocket in self.active_connections.items():
            # Check if client is subscribed to this channel
            if channel == "all" or channel in self.client_subscriptions.get(client_id, set()):
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to {client_id}: {e}")
                    disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)
    
    async def _redis_listener(self):
        """Listen to Redis pub/sub and broadcast to clients"""
        if not self.redis:
            return
        
        pubsub = self.redis.pubsub()
        
        # Subscribe to all relevant channels
        await pubsub.subscribe(
            "market:price:all",
            "market:news:breaking",
            "market:health",
            "events:price_move",
            "events:volume_spike",
            "events:breaking_news",
            "ai:analysis:complete",
        )
        
        logger.info("Redis listener started")
        
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await self._handle_redis_message(message)
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            await pubsub.close()
    
    async def _handle_redis_message(self, message: Dict[str, Any]):
        """Handle Redis pub/sub message and broadcast to clients"""
        channel = message.get("channel", "")
        data_str = message.get("data", "")
        
        if not data_str or not isinstance(data_str, str):
            return
        
        try:
            data = json.loads(data_str)
            
            # Add metadata
            data["channel"] = channel
            data["server_time"] = datetime.now().isoformat()
            
            # Broadcast to subscribed clients
            await self.broadcast(data, channel)
            
        except json.JSONDecodeError:
            logger.error(f"Failed to decode Redis message: {data_str}")
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/market")
async def websocket_market_endpoint(
    websocket: WebSocket,
    token: Optional[str] = None,
):
    """
    WebSocket endpoint for real-time market data.
    
    Message format:
    {
        "action": "subscribe" | "unsubscribe" | "ping",
        "channels": ["market:price:AAPL", "market:news:breaking"],
        "data": {...}
    }
    
    Channels:
    - market:price:{ticker} - Live price updates for specific ticker
    - market:price:all - All price updates
    - market:news:breaking - Breaking news headlines
    - market:health - Market-wide health metrics
    - events:price_move - Significant price movements
    - events:volume_spike - Volume anomalies
    - events:breaking_news - Critical news events
    - ai:analysis:complete - AI analysis results
    """
    
    # Generate client ID
    client_id = f"client_{id(websocket)}"
    
    # Authenticate (optional, can be enforced)
    # user = await get_current_user_ws(token) if token else None
    
    await manager.connect(client_id, websocket)
    
    try:
        # Send welcome message
        await manager.send_personal_message({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
        }, client_id)
        
        # Listen for client messages
        while True:
            data = await websocket.receive_json()
            
            action = data.get("action")
            channels = data.get("channels", [])
            
            if action == "subscribe":
                await manager.subscribe(client_id, channels)
                await manager.send_personal_message({
                    "type": "subscription",
                    "status": "subscribed",
                    "channels": channels,
                }, client_id)
                
            elif action == "unsubscribe":
                await manager.unsubscribe(client_id, channels)
                await manager.send_personal_message({
                    "type": "subscription",
                    "status": "unsubscribed",
                    "channels": channels,
                }, client_id)
                
            elif action == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                }, client_id)
                
            else:
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown action: {action}",
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket server status"""
    return {
        "active_connections": len(manager.active_connections),
        "total_subscriptions": sum(len(subs) for subs in manager.client_subscriptions.values()),
        "redis_connected": manager.redis is not None,
        "timestamp": datetime.now().isoformat(),
    }
