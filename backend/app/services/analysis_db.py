from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

AGENT_ORDER = [
    "planner",
    "market_research",
    "financial_analysis",
    "technical_analysis",
    "news_sentiment",
    "risk_analysis",
    "portfolio_allocation",
    "report_generation",
]


async def insert_session(
    db: Any,
    session_id: str,
    user_input: dict[str, Any],
    user_id: str | None = None,
) -> None:
    # PostgreSQL doesn't need WAL mode pragmas
    await db.execute(
        """
        INSERT INTO analysis_sessions (id, user_id, user_input, status)
        VALUES (?, ?, ?, 'processing')
        """,
        (session_id, user_id, json.dumps(user_input)),
    )
    for name in AGENT_ORDER:
        await db.execute(
            """
            INSERT INTO agent_progress (session_id, agent_name, status)
            VALUES (?, ?, 'pending')
            """,
            (session_id, name),
        )
    await db.commit()


async def set_agent_status(
    db: Any,
    session_id: str,
    agent_name: str,
    status: str,
    error: str | None = None,
) -> None:
    await db.execute(
        """
        UPDATE agent_progress SET status = ?, error = ?
        WHERE session_id = ? AND agent_name = ?
        """,
        (status, error, session_id, agent_name),
    )
    await db.commit()


async def finalize_session(
    db: Any,
    session_id: str,
    *,
    status: str,
    summary: dict[str, Any] | None = None,
    market_data: dict[str, Any] | None = None,
    technical_data: dict[str, Any] | None = None,
    portfolio: dict[str, Any] | None = None,
    report: str = "",
    report_id: str = "",
) -> None:
    # Use naive UTC datetime for PostgreSQL (remove tzinfo)
    completed_at = datetime.now(UTC).replace(tzinfo=None)
    
    await db.execute(
        """
        UPDATE analysis_sessions
        SET status = ?, summary = ?, market_data = ?, technical_data = ?,
            portfolio = ?, report = ?, report_id = ?, completed_at = ?
        WHERE id = ?
        """,
        (
            status,
            json.dumps(summary) if summary is not None else None,
            json.dumps(market_data) if market_data is not None else None,
            json.dumps(technical_data) if technical_data is not None else None,
            json.dumps(portfolio) if portfolio is not None else None,
            report,
            report_id,
            completed_at,
            session_id,
        ),
    )
    await db.commit()


async def load_session_row(db: Any, session_id: str) -> dict[str, Any] | None:
    cur = await db.execute(
        """SELECT id, user_id, user_input, status, summary, market_data, technical_data, portfolio,
                  report, report_id, completed_at FROM analysis_sessions WHERE id = ?""",
        (session_id,),
    )
    row = await cur.fetchone()
    if not row:
        return None
    # Convert asyncpg Record to dict if needed
    return dict(row) if hasattr(row, 'keys') else row


async def load_user_sessions(db: Any, user_id: str, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
    cur = await db.execute(
        """
        SELECT id, status, summary, created_at, completed_at
        FROM analysis_sessions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset),
    )
    rows = await cur.fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "id": r["id"],
                "status": r["status"],
                "summary": json.loads(r["summary"]) if r["summary"] else None,
                "created_at": r["created_at"],
                "completed_at": r["completed_at"],
            }
        )
    return out


async def load_agent_progress(db: Any, session_id: str) -> list[dict[str, Any]]:
    cur = await db.execute(
        """
        SELECT agent_name, status, error FROM agent_progress
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    )
    rows = await cur.fetchall()
    return [dict(r) for r in rows]
