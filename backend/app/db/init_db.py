import json
from collections.abc import AsyncGenerator
from pathlib import Path

import aiosqlite

from app.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id TEXT PRIMARY KEY,
    user_input TEXT NOT NULL,
    status TEXT DEFAULT 'processing',
    summary TEXT,
    market_data TEXT,
    technical_data TEXT,
    portfolio TEXT,
    report TEXT,
    report_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    error TEXT,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    ticker TEXT NOT NULL UNIQUE,
    ticker_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

CREATE TABLE IF NOT EXISTS stock_cache (
    ticker TEXT NOT NULL,
    data_type TEXT NOT NULL,
    data TEXT NOT NULL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data_type)
);

CREATE INDEX IF NOT EXISTS idx_agent_progress_session ON agent_progress(session_id);
CREATE INDEX IF NOT EXISTS idx_watchlist_ticker ON watchlist(ticker);
"""


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


async def init_db() -> None:
    path = settings.database_path
    if not path.is_absolute():
        path = Path.cwd() / path
    _ensure_parent_dir(path)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def get_connection() -> aiosqlite.Connection:
    path = settings.database_path
    if not path.is_absolute():
        path = Path.cwd() / path
    _ensure_parent_dir(path)
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    return db


async def connection_cm() -> AsyncGenerator[aiosqlite.Connection, None]:
    db = await get_connection()
    try:
        yield db
    finally:
        await db.close()
