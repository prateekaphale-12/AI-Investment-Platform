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
        user_id = row["user_id"]
        
        # Query database ONCE to get user's LLM settings
        llm_config = await _load_user_llm_config(db, user_id)
        
        # Pass config to graph - it will be available in state for all nodes
        await run_graph(db, session_id, user_input, llm_config)
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


async def _load_user_llm_config(db: Any, user_id: str) -> dict[str, Any]:
    """Load user's LLM configuration from database (single query).
    
    Returns dict with structure:
    {
        "provider": "groq",
        "model": "llama-3.1-8b-instant",
        "api_key": "gsk_...",
        "has_api_key": True
    }
    """
    try:
        cur = await db.execute(
            "SELECT provider, model, api_key_encrypted FROM user_llm_settings WHERE user_id = ?",
            (user_id,)
        )
        row = await cur.fetchone()
        
        if not row:
            # No settings saved, use defaults
            return {
                "provider": "groq",
                "model": "llama-3.1-8b-instant",
                "api_key": None,
                "has_api_key": False
            }
        
        # Decrypt API key
        from app.services.llm_settings_service import decrypt_api_key
        api_key = decrypt_api_key(row["api_key_encrypted"])
        
        return {
            "provider": row["provider"],
            "model": row["model"],
            "api_key": api_key,
            "has_api_key": bool(api_key)
        }
    except Exception as e:
        logger.error(f"Failed to load LLM config: {e}")
        # Return defaults on error
        return {
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "api_key": None,
            "has_api_key": False
        }
