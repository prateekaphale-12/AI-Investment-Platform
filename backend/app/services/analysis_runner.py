from __future__ import annotations

import json
from typing import Any

from loguru import logger

from app.agents.graph.graph import run_graph
from app.db.init_db import get_connection
from app.services import analysis_db as adb


async def execute_analysis(session_id: str) -> None:
    """Background job: loads session input, runs LangGraph, persists results."""
    db = await get_connection()
    try:
        row = await adb.load_session_row(db, session_id)
        if not row:
            logger.error("execute_analysis: session {} not found", session_id)
            return
        user_input = json.loads(row["user_input"])
        await run_graph(db, session_id, user_input)
    except Exception as e:
        logger.exception("execute_analysis failed: {}", e)
        await adb.finalize_session(
            db,
            session_id,
            status="failed",
            summary={"error": str(e)},
            market_data={},
            technical_data={},
            portfolio={},
            report="",
            report_id="",
        )
    finally:
        await db.close()
