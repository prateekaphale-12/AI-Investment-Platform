from collections.abc import AsyncGenerator
import os

import asyncpg
from loguru import logger

from app.db.database import PgConnectionAdapter


def _settings():
    """Read config at call time so tests may replace ``app.config.settings``."""
    import app.config as app_config

    return app_config.settings

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

CREATE TABLE IF NOT EXISTS user_llm_settings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_llm_settings_user_id ON user_llm_settings(user_id);
"""


async def init_db() -> None:
    """Initialize PostgreSQL database with all required tables."""
    settings = _settings()
    db_url = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL')
    
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required. SQLite is no longer supported.")
    
    conn = await asyncpg.connect(db_url)
    try:
        # Execute all schema statements
        for stmt in filter(None, [s.strip() for s in SCHEMA_PG.split(";")]):
            if stmt.strip():
                await conn.execute(stmt)
        
        # Add any missing columns to existing tables (for migrations)
        await conn.execute(
            "ALTER TABLE analysis_sessions ADD COLUMN IF NOT EXISTS user_id TEXT"
        )
        await conn.execute("ALTER TABLE watchlist ADD COLUMN IF NOT EXISTS user_id TEXT")
        
        # Create indexes
        await conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_watchlist_user_ticker ON watchlist(user_id, ticker)"
        )
        
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        await conn.close()


async def get_connection():
    """Get PostgreSQL connection."""
    settings = _settings()
    db_url = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL')
    
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required. SQLite is no longer supported.")
    
    conn = await asyncpg.connect(db_url)
    return PgConnectionAdapter(conn)


async def connection_cm() -> AsyncGenerator[asyncpg.Connection, None]:
    """Context manager for database connections."""
    conn = await asyncpg.connect(
        getattr(_settings(), 'database_url', None) or os.getenv('DATABASE_URL')
    )
    try:
        yield conn
    finally:
        await conn.close()
