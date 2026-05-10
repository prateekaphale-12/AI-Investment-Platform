from fastapi import APIRouter

from app.config import settings
from app.models.domain import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/capabilities")
async def capabilities() -> dict[str, bool | str]:
    return {
        "gemini_configured": bool(settings.gemini_api_key),
        "gemini_model": settings.gemini_model,
    }
