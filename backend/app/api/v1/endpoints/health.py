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
        "openai_configured": bool(getattr(settings, 'openai_api_key', None)),
        "openai_model": getattr(settings, 'openai_model', 'gpt-3.5-turbo'),
        "groq_configured": bool(getattr(settings, 'groq_api_key', None)),
        "groq_model": getattr(settings, 'groq_model', 'llama-3.1-8b-instant'),
    }
