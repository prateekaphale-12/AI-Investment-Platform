#!/usr/bin/env python3
"""
Migration script to add user_llm_settings table
Run this to add the new table for storing user LLM preferences
"""

import asyncio
from pathlib import Path

import aiosqlite
from app.config import settings
from app.db.database import SqliteConnectionAdapter


async def add_user_llm_settings_table():
    """Add user_llm_settings table to existing database"""
    db_path = settings.database_path
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    
    print(f"Adding user_llm_settings table to: {db_path}")
    
    async with aiosqlite.connect(db_path) as db:
        # Check if table already exists
        cursor = await db.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_llm_settings'
        """)
        if await cursor.fetchone():
            print("Table user_llm_settings already exists")
            return
        
        # Create the table
        await db.execute("""
            CREATE TABLE user_llm_settings (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                api_key_encrypted TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, provider)
            )
        """)
        
        # Create index for performance
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_llm_settings_user_id 
            ON user_llm_settings(user_id)
        """)
        
        await db.commit()
        print("user_llm_settings table created successfully")


if __name__ == "__main__":
    asyncio.run(add_user_llm_settings_table())
