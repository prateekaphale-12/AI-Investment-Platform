from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.init_db import get_connection
from app.models.domain import WatchlistAddRequest, WatchlistItem, WatchlistItemsResponse

router = APIRouter()


class WatchlistAddResponse(BaseModel):
    status: str = "added"


class WatchlistDeleteResponse(BaseModel):
    status: str = "removed"


@router.post("/watchlist", response_model=WatchlistAddResponse)
async def add_watchlist(body: WatchlistAddRequest) -> WatchlistAddResponse:
    db = await get_connection()
    try:
        wid = str(uuid4())
        await db.execute(
            """
            INSERT INTO watchlist (id, session_id, ticker, ticker_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                session_id = excluded.session_id,
                ticker_name = excluded.ticker_name
            """,
            (wid, body.session_id, body.ticker.upper(), body.ticker_name),
        )
        await db.commit()
        return WatchlistAddResponse()
    finally:
        await db.close()


@router.delete("/watchlist/{ticker}", response_model=WatchlistDeleteResponse)
async def remove_watchlist(ticker: str) -> WatchlistDeleteResponse:
    db = await get_connection()
    try:
        await db.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        await db.commit()
        return WatchlistDeleteResponse()
    finally:
        await db.close()


@router.get("/watchlist", response_model=WatchlistItemsResponse)
async def list_watchlist() -> WatchlistItemsResponse:
    db = await get_connection()
    try:
        cur = await db.execute(
            """
            SELECT w.id, w.session_id, w.ticker, w.ticker_name, w.added_at,
                   a.summary as last_analysis
            FROM watchlist w
            LEFT JOIN analysis_sessions a ON w.session_id = a.id
            ORDER BY w.added_at DESC
            """
        )
        rows = await cur.fetchall()
        items = [
            WatchlistItem(
                id=r["id"],
                session_id=r["session_id"],
                ticker=r["ticker"],
                ticker_name=r["ticker_name"],
                added_at=str(r["added_at"]),
            )
            for r in rows
        ]
        return WatchlistItemsResponse(items=items)
    finally:
        await db.close()
