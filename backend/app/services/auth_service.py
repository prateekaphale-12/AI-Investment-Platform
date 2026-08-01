from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings
from app.db.init_db import get_connection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Redis connection for token blacklist
_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Get or create Redis connection for token blacklist."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algo, salt_b64, digest_b64 = password_hash.split("$", 2)
        if algo != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode())
        expected = base64.b64decode(digest_b64.encode())
        current = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(current, expected)
    except Exception:
        return False


def create_access_token(subject: str) -> str:
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    # Convert datetime to Unix timestamp (integer) for JSON serialization
    # Ensure subject is a string (handles UUID objects from database)
    payload = {"sub": str(subject), "exp": int(expires.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def create_user(email: str, password: str) -> dict[str, Any]:
    db = await get_connection()
    try:
        row = await db.fetchrow("SELECT id FROM users WHERE email = $1", email.lower())
        if row:
            raise HTTPException(status_code=400, detail="Email already registered")
        uid = str(uuid4())
        await db.execute(
            "INSERT INTO users (id, email, password_hash) VALUES ($1, $2, $3)",
            uid, email.lower(), hash_password(password)
        )
        return {"id": uid, "email": email.lower()}
    finally:
        await db.close()


async def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    db = await get_connection()
    try:
        row = await db.fetchrow("SELECT id, email, password_hash FROM users WHERE email = $1", email.lower())
        if not row:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        # Ensure id is always a string (handles UUID objects from asyncpg)
        return {"id": str(row["id"]), "email": row["email"]}
    finally:
        await db.close()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if token is blacklisted
    redis_client = await get_redis()
    is_blacklisted = await redis_client.get(f"blacklist:{token}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db = await get_connection()
    try:
        row = await db.fetchrow("SELECT id, email FROM users WHERE id = $1", user_id)
        if not row:
            raise credentials_exception
        # Ensure id is always a string (handles UUID objects from asyncpg)
        return {"id": str(row["id"]), "email": row["email"]}
    finally:
        await db.close()


async def revoke_token(token: str) -> None:
    """
    Add token to blacklist in Redis.
    Token will expire automatically based on JWT expiration time.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        exp = payload.get("exp")
        if not exp:
            return
        
        # Calculate TTL (time until token expires)
        now = int(datetime.now(UTC).timestamp())
        ttl = max(exp - now, 0)
        
        if ttl > 0:
            redis_client = await get_redis()
            # Add to blacklist with expiration
            await redis_client.setex(f"blacklist:{token}", ttl, "1")
    except JWTError:
        # Token is invalid anyway, no need to blacklist
        pass

