from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field

from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
)

router = APIRouter(prefix="/auth")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


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

