#!/usr/bin/env python3
"""
Migration script to create PostgreSQL tables
Run this to initialize PostgreSQL database with all required tables
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.config import settings

async def create_postgres_tables():
    """Create all required tables in PostgreSQL"""
    
    # Parse DATABASE_URL to get connection details
    db_url = getattr(settings, 'database_url', None) or os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        return
    
    print(f"Creating PostgreSQL tables at: {db_url}")
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(db_url)
        
        # Create users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create user_llm_settings table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_llm_settings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                provider VARCHAR(50) NOT NULL,
                model VARCHAR(100) NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, provider)
            )
        """)
        
        # Create analysis_sessions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS analysis_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                user_input JSONB NOT NULL,
                status VARCHAR(50) DEFAULT 'processing',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create agent_progress table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_progress (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID NOT NULL REFERENCES analysis_sessions(id) ON DELETE CASCADE,
                agent_name VARCHAR(100) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, agent_name)
            )
        """)
        
        # Create watchlist table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ticker VARCHAR(10) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, ticker)
            )
        """)
        
        # Create stock_cache table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_cache (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                ticker VARCHAR(10) NOT NULL,
                data_type VARCHAR(50) NOT NULL,
                data JSONB NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, data_type)
            )
        """)
        
        # Create indexes for performance
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_llm_settings_user_id ON user_llm_settings(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_sessions_user_id ON analysis_sessions(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_progress_session_id ON agent_progress(session_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_stock_cache_ticker ON stock_cache(ticker)")
        
        await conn.close()
        print("✅ PostgreSQL tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating PostgreSQL tables: {e}")

if __name__ == "__main__":
    asyncio.run(create_postgres_tables())
