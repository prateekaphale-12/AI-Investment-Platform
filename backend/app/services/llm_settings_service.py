from __future__ import annotations

import base64
from typing import Any, Dict

from cryptography.fernet import Fernet
from loguru import logger

from app.config import settings
from app.db.init_db import get_connection


def _get_encryption_key() -> bytes:
    """Get encryption key for API keys"""
    # Use JWT secret as encryption key, properly base64-encoded for Fernet
    import base64
    key = settings.jwt_secret_key.encode()
    # Pad or truncate to 32 bytes, then base64 encode
    key_bytes = key[:32].ljust(32, b'0')
    return base64.urlsafe_b64encode(key_bytes)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for storage"""
    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(api_key.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key from storage"""
    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted = base64.b64decode(encrypted_key.encode())
        return fernet.decrypt(encrypted).decode()
    except Exception as e:
        logger.error(f"Failed to decrypt API key: {e}")
        return ""


async def save_user_llm_settings(user_id: str, provider: str, model: str, api_key: str) -> bool:
    """Save user's LLM settings to database"""
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            db = await get_connection()
            
            # Encrypt API key before storing
            encrypted_key = encrypt_api_key(api_key)
            
            # Check if settings already exist for this user
            cur = await db.execute(
                "SELECT id FROM user_llm_settings WHERE user_id = ?",
                (user_id,)
            )
            existing = await cur.fetchone()
            
            if existing:
                # Update existing settings
                await db.execute(
                    """UPDATE user_llm_settings 
                       SET provider = ?, model = ?, api_key_encrypted = ?, updated_at = CURRENT_TIMESTAMP 
                       WHERE user_id = ?""",
                    (provider, model, encrypted_key, user_id)
                )
            else:
                # Insert new settings
                from uuid import uuid4
                settings_id = str(uuid4())
                await db.execute(
                    """INSERT INTO user_llm_settings 
                       (id, user_id, provider, model, api_key_encrypted, created_at, updated_at) 
                       VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (settings_id, user_id, provider, model, encrypted_key)
                )
            
            await db.commit()
            logger.info(f"Saved LLM settings for user {user_id}, provider {provider}")
            return True
            
        except Exception as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Database locked, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})")
                import asyncio
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                logger.error(f"Failed to save LLM settings: {e}")
                return False
        finally:
            try:
                await db.close()
            except:
                pass


async def get_user_llm_settings(user_id: str) -> Dict[str, Any]:
    """Get user's LLM settings from database"""
    db = await get_connection()
    try:
        cur = await db.execute(
            """SELECT provider, model, api_key_encrypted, updated_at 
               FROM user_llm_settings 
               WHERE user_id = ?""",
            (user_id,)
        )
        row = await cur.fetchone()
        
        if not row:
            return {}
        
        # Decrypt API key
        decrypted_key = decrypt_api_key(row["api_key_encrypted"])
        
        return {
            row["provider"]: {
                "provider": row["provider"],
                "model": row["model"],
                "api_key": decrypted_key,
                "has_api_key": bool(decrypted_key),
                "updated_at": row["updated_at"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get LLM settings: {e}")
        return {}
    finally:
        await db.close()


async def check_llm_connection(provider: str, api_key: str) -> Dict[str, Any]:
    """Test LLM connection with provided credentials"""
    try:
        # Direct Groq test for now, extend for other providers later
        if provider == "groq":
            from groq import AsyncGroq
            
            client = AsyncGroq(api_key=api_key)
            
            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "user", "content": "What is 2+2? Answer with just the number."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "4":
                return {
                    "success": True,
                    "response": result,
                    "provider": provider
                }
            else:
                return {
                    "success": False,
                    "error": f"API key validation failed. Expected '4' but got: {result}",
                    "provider": provider
                }
                
        elif provider == "openai":
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": "What is 2+2? Answer with just the number."}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == "4":
                return {
                    "success": True,
                    "response": result,
                    "provider": provider
                }
            else:
                return {
                    "success": False,
                    "error": f"API key validation failed. Expected '4' but got: {result}",
                    "provider": provider
                }
        else:
            return {
                "success": False,
                "error": f"Unsupported provider: {provider}",
                "provider": provider
            }
            
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle common API key errors
        if "invalid_api_key" in error_msg or "unauthorized" in error_msg:
            return {
                "success": False,
                "error": "Invalid API key. Please check your Groq API key and try again.",
                "provider": provider
            }
        elif "rate" in error_msg or "quota" in error_msg:
            return {
                "success": False,
                "error": "Rate limit exceeded. Please try again later.",
                "provider": provider
            }
        elif "connection" in error_msg or "network" in error_msg:
            return {
                "success": False,
                "error": "Connection error. Please check your internet connection and try again.",
                "provider": provider
            }
        else:
            return {
                "success": False,
                "error": f"Connection test failed: {str(e)}",
                "provider": provider
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "provider": provider
        }
