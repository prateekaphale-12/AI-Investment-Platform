from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
    oauth2_scheme,
    revoke_token,
)

router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
async def register(body: RegisterRequest) -> dict:
    user = await create_user(body.email, body.password)
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login")
async def login(body: LoginRequest) -> dict:
    user = await authenticate_user(body.email, body.password)
    if not user:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["id"])
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user), token: str = Depends(oauth2_scheme)) -> dict:
    """
    Logout endpoint - revokes the current JWT token.
    
    Note: This adds the token to a blacklist in Redis.
    Client should also clear the token from localStorage.
    """
    # The token is validated by get_current_user dependency
    # We just need to add it to the blacklist
    await revoke_token(token)
    return {"message": "Successfully logged out"}


