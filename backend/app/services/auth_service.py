from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import aiosqlite
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings
from app.db.init_db import get_connection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


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
    payload = {"sub": subject, "exp": int(expires.timestamp())}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def create_user(email: str, password: str) -> dict[str, Any]:
    db = await get_connection()
    try:
        cur = await db.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
        if await cur.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        uid = str(uuid4())
        await db.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            (uid, email.lower(), hash_password(password)),
        )
        await db.commit()
        return {"id": uid, "email": email.lower()}
    finally:
        await db.close()


async def authenticate_user(email: str, password: str) -> dict[str, Any] | None:
    db = await get_connection()
    try:
        cur = await db.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email.lower(),))
        row = await cur.fetchone()
        if not row:
            return None
        if not verify_password(password, row["password_hash"]):
            return None
        return {"id": row["id"], "email": row["email"]}
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
    db = await get_connection()
    try:
        cur = await db.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            raise credentials_exception
        return {"id": row["id"], "email": row["email"]}
    finally:
        await db.close()
