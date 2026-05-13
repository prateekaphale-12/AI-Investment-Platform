from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.init_db import get_connection
from app.models.domain import WatchlistAddRequest, WatchlistItem, WatchlistItemsResponse
from app.services.auth_service import get_current_user

router = APIRouter()


class WatchlistAddResponse(BaseModel):
    status: str = "added"


class WatchlistDeleteResponse(BaseModel):
    status: str = "removed"


@router.post("/watchlist", response_model=WatchlistAddResponse)
async def add_watchlist(body: WatchlistAddRequest, current_user: dict = Depends(get_current_user)) -> WatchlistAddResponse:
    db = await get_connection()
    try:
        wid = str(uuid4())
        await db.execute(
            """
            INSERT INTO watchlist (id, user_id, session_id, ticker, ticker_name)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                session_id = excluded.session_id,
                ticker_name = excluded.ticker_name
            """,
            (wid, current_user["id"], body.session_id, body.ticker.upper(), body.ticker_name),
        )
        await db.commit()
        return WatchlistAddResponse()
    finally:
        await db.close()


@router.delete("/watchlist/{ticker}", response_model=WatchlistDeleteResponse)
async def remove_watchlist(ticker: str, current_user: dict = Depends(get_current_user)) -> WatchlistDeleteResponse:
    db = await get_connection()
    try:
        await db.execute("DELETE FROM watchlist WHERE ticker = ? AND user_id = ?", (ticker.upper(), current_user["id"]))
        await db.commit()
        return WatchlistDeleteResponse()
    finally:
        await db.close()


@router.get("/watchlist", response_model=WatchlistItemsResponse)
async def list_watchlist(current_user: dict = Depends(get_current_user)) -> WatchlistItemsResponse:
    db = await get_connection()
    try:
        cur = await db.execute(
            """
            SELECT w.id, w.session_id, w.ticker, w.ticker_name, w.added_at,
                   a.summary as last_analysis
            FROM watchlist w
            LEFT JOIN analysis_sessions a ON w.session_id = a.id
            WHERE w.user_id = ?
            ORDER BY w.added_at DESC
            """,
            (current_user["id"],),
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
