from collections.abc import AsyncGenerator
from pathlib import Path
import os

import aiosqlite
import asyncpg

from app.db.database import PgConnectionAdapter, SqliteConnectionAdapter


def _settings():
    """Read config at call time so tests may replace ``app.config.settings`` (isolated SQLite)."""
    import app.config as app_config

    return app_config.settings

# SQLite: create tables first. Do not create idx_watchlist_user_ticker until after
# optional ALTERs — existing DB files may predate user_id columns, and SQLite will
# error on "CREATE INDEX ... (user_id, ...)" if the column does not exist yet.
SCHEMA_TABLES_SQLITE = """
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
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
    user_id TEXT,
    session_id TEXT,
    ticker TEXT NOT NULL,
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

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_market_snapshot (
    snapshot_date TEXT PRIMARY KEY,
    picks_json TEXT NOT NULL,
    gainers_json TEXT NOT NULL,
    losers_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT,
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
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    error TEXT
);

CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    session_id TEXT,
    ticker TEXT NOT NULL,
    ticker_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_market_snapshot (
    snapshot_date TEXT PRIMARY KEY,
    picks_json TEXT NOT NULL,
    gainers_json TEXT NOT NULL,
    losers_json TEXT NOT NULL,
    metrics_json TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


async def init_db() -> None:
    settings = _settings()
    db_url = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL')
    if db_url:
        conn = await asyncpg.connect(db_url)
        try:
            for stmt in filter(None, [s.strip() for s in SCHEMA_PG.split(";")]):
                await conn.execute(stmt)
            await conn.execute(
                "ALTER TABLE analysis_sessions ADD COLUMN IF NOT EXISTS user_id TEXT"
            )
            await conn.execute("ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS user_id TEXT")
            await conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_ticker ON watchlist(user_id, ticker)"
            )
        finally:
            await conn.close()
        return
    path = settings.database_path
    if not path.is_absolute():
        path = Path.cwd() / path
    _ensure_parent_dir(path)
    async with aiosqlite.connect(path) as db:
        await db.executescript(SCHEMA_TABLES_SQLITE)
        # Lightweight alignment for SQLite files created before auth columns existed.
        # Skip PRAGMA commands for PostgreSQL
        if not db_url:
            cur = await db.execute("PRAGMA table_info(analysis_sessions)")
            cols = [r[1] for r in await cur.fetchall()]
            if "user_id" not in cols:
                await db.execute("ALTER TABLE analysis_sessions ADD COLUMN user_id TEXT")
            cur = await db.execute("PRAGMA table_info(watchlist)")
            wcols = [r[1] for r in await cur.fetchall()]
            if "user_id" not in wcols:
                await db.execute("ALTER TABLE watchlist ADD COLUMN user_id TEXT")
        await db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_ticker ON watchlist(user_id, ticker)"
        )
        await db.commit()


async def get_connection():
    settings = _settings()
    db_url = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL')
    if db_url:
        conn = await asyncpg.connect(db_url)
        return PgConnectionAdapter(conn)
    path = settings.database_path
    if not path.is_absolute():
        path = Path.cwd() / path
    _ensure_parent_dir(path)
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    return SqliteConnectionAdapter(db)


async def connection_cm() -> AsyncGenerator[aiosqlite.Connection, None]:
    db = await get_connection()
    try:
        yield db
    finally:
        await db.close()
