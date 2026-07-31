"""Pytest configuration and fixtures for test suite."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator

import asyncpg
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_database_url() -> str:
    """Get or create test database URL from environment or use default."""
    # Try to get from environment variable
    db_url = os.getenv("TEST_DATABASE_URL")
    
    if db_url:
        return db_url
    
    # Default to a test database on localhost
    # This assumes PostgreSQL is running (same as docker-compose)
    return "postgresql://postgres:postgres@localhost:5432/investment_platform_test"


@pytest.fixture(scope="function")
async def clean_test_db(test_database_url: str) -> AsyncGenerator[str, None]:
    """Create clean test database for each test."""
    conn = None
    try:
        # Connect to database
        conn = await asyncpg.connect(test_database_url)
        
        # Clean all tables
        await conn.execute("DROP SCHEMA public CASCADE")
        await conn.execute("CREATE SCHEMA public")
        await conn.execute("GRANT ALL ON SCHEMA public TO postgres")
        await conn.execute("GRANT ALL ON SCHEMA public TO public")
        
        # Initialize schema
        from app.db.init_db import SCHEMA_PG
        
        for stmt in filter(None, [s.strip() for s in SCHEMA_PG.split(";")]):
            if stmt.strip():
                await conn.execute(stmt)
        
        yield test_database_url
        
    finally:
        if conn:
            await conn.close()


@pytest.fixture
def client(clean_test_db: str, monkeypatch) -> Generator[TestClient, None, None]:
    """Create test client with clean PostgreSQL database."""
    import app.config as cfg
    
    # Set database URL to test database
    monkeypatch.setenv("DATABASE_URL", clean_test_db)
    monkeypatch.setattr(cfg.settings, "database_url", clean_test_db)
    
    # Import app after setting environment
    from app.main import app
    
    with TestClient(app) as c:
        yield c
