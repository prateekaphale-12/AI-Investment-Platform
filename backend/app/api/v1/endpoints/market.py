from __future__ import annotations

from fastapi import APIRouter

from app.services.snapshot_service import generate_daily_snapshot, get_latest_snapshot

router = APIRouter()


@router.get("/market/daily-snapshot")
async def market_snapshot() -> dict:
    snap = await get_latest_snapshot()
    if snap:
        return snap
    return await generate_daily_snapshot()

