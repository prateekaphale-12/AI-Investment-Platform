from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

from app.config import settings

_client: Redis | None = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def cache_get_json(key: str) -> dict[str, Any] | None:
    try:
        value = await get_redis().get(key)
        if not value:
            return None
        data = json.loads(value)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


async def cache_set_json(key: str, value: dict[str, Any], ttl_seconds: int = 3600) -> None:
    try:
        await get_redis().set(key, json.dumps(value), ex=ttl_seconds)
    except Exception:
        return

