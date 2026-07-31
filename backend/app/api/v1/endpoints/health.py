from fastapi import APIRouter, Depends
from app.config import settings
from app.models.domain import HealthResponse
from app.services.llm_settings_service import get_user_llm_settings
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/capabilities")
async def capabilities(current_user: dict = Depends(get_current_user)) -> dict[str, bool | str | None]:
    """Get user's AI configuration from database"""
    user_id = current_user.get("id")
    
    # Get user's saved LLM settings from database
    user_settings = await get_user_llm_settings(user_id)
    
    if user_settings and user_settings.get("provider"):
        # User has configured an LLM
        provider = user_settings.get("provider", "")
        model = user_settings.get("model", "")
        has_api_key = user_settings.get("has_api_key", False)
        
        return {
            "ai_configured": has_api_key,
            "provider": provider,
            "model": model,
            "openai_configured": provider == "openai" and has_api_key,
            "groq_configured": provider == "groq" and has_api_key,
        }
    else:
        # No user configuration - AI not configured
        return {
            "ai_configured": False,
            "provider": None,
            "model": None,
            "openai_configured": False,
            "groq_configured": False,
        }
