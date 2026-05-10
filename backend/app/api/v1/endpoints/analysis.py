from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.db.init_db import get_connection
from app.models.domain import AnalysisStatusResponse, AnalyzeRequest
from app.services import analysis_db as adb
from app.services.analysis_runner import execute_analysis
from app.services.stock_service import fetch_price_history

router = APIRouter(prefix="")


class AnalyzeAccepted(BaseModel):
    session_id: str = Field(...)
    status: str = Field(default="processing")


@router.post("/analyze", status_code=202, response_model=AnalyzeAccepted)
async def start_analysis(payload: AnalyzeRequest, background_tasks: BackgroundTasks) -> AnalyzeAccepted:
    from uuid import uuid4

    session_id = str(uuid4())

    ui = payload.model_dump()
    db = await get_connection()
    try:
        await adb.insert_session(db, session_id, ui)
        background_tasks.add_task(execute_analysis, session_id)
    finally:
        await db.close()

    return AnalyzeAccepted(session_id=session_id, status="processing")


@router.get("/analysis/{session_id}/status", response_model=AnalysisStatusResponse)
async def analysis_status(session_id: str) -> AnalysisStatusResponse:
    db = await get_connection()
    try:
        row = await adb.load_session_row(db, session_id)
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        steps = await adb.load_agent_progress(db, session_id)
        sess_status = row["status"]
        current = None
        done = sum(1 for s in steps if s["status"] == "completed")
        for s in steps:
            if s["status"] == "running":
                current = s["agent_name"]
        errs = [f"{s['agent_name']}: {s['error']}" for s in steps if s["error"]]
        agents_total = len(adb.AGENT_ORDER)
        if sess_status == "failed":
            return AnalysisStatusResponse(
                session_id=session_id,
                status="failed",
                current_agent=current,
                agents_completed=done,
                agents_total=agents_total,
                errors=errs,
            )
        if sess_status == "completed":
            return AnalysisStatusResponse(
                session_id=session_id,
                status="completed",
                current_agent=None,
                agents_completed=agents_total,
                agents_total=agents_total,
                errors=errs,
            )
        return AnalysisStatusResponse(
            session_id=session_id,
            status="processing",
            current_agent=current,
            agents_completed=done,
            agents_total=agents_total,
            errors=errs,
        )
    finally:
        await db.close()


@router.get("/analysis/{session_id}/results")
async def analysis_results(session_id: str) -> dict[str, Any]:
    db = await get_connection()
    try:
        row = await adb.load_session_row(db, session_id)
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

        def _loads(s: str | None, default: Any) -> Any:
            if not s:
                return default
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return default

        portfolio = _loads(row["portfolio"], {})
        steps = await adb.load_agent_progress(db, session_id)
        errs = [f"{s['agent_name']}: {s['error']}" for s in steps if s.get("error")]

        return {
            "session_id": session_id,
            "status": row["status"],
            "summary": _loads(row["summary"], None),
            "market_data": _loads(row["market_data"], {}),
            "technical_data": _loads(row["technical_data"], {}),
            "portfolio": portfolio,
            "report": row["report"] or "",
            "report_id": row["report_id"] or "",
            "errors": errs,
        }
    finally:
        await db.close()


@router.get("/analysis/{session_id}/report")
async def analysis_report(session_id: str) -> dict[str, str]:
    db = await get_connection()
    try:
        row = await adb.load_session_row(db, session_id)
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"report_id": row["report_id"] or "", "markdown": row["report"] or ""}
    finally:
        await db.close()


@router.get("/stocks/{ticker}/price")
async def stock_price_history(ticker: str, period: str = "1y") -> dict[str, Any]:
    p_map = {"1M": "1mo", "6M": "6mo", "1Y": "1y", "1mo": "1mo", "6mo": "6mo", "1y": "1y"}
    yf_period = p_map.get(period, period)
    db = await get_connection()
    try:
        df = await fetch_price_history(db, ticker.upper(), yf_period)
        if df is None or df.empty:
            return {"ticker": ticker.upper(), "period": yf_period, "points": []}
        points = []
        for _, r in df.iterrows():
            d = r.get("date")
            dt = str(d) if d is not None else None
            points.append({"date": dt, "close": float(r["Close"]), "volume": float(r.get("Volume", 0))})
        await db.commit()
        return {"ticker": ticker.upper(), "period": yf_period, "points": points}
    finally:
        await db.close()
