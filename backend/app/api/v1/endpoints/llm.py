from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from app.services.llm_service import get_available_providers, LLMProvider
from app.services.auth_service import get_current_user
from app.services.llm_settings_service import save_user_llm_settings, get_user_llm_settings, check_llm_connection

router = APIRouter()


class LLMSettingsRequest(BaseModel):
    provider: str
    api_key: str


class LLMTestRequest(BaseModel):
    provider: str
    api_key: str


class LLMSettingsResponse(BaseModel):
    provider: str
    model: str
    has_api_key: bool
    settings: dict[str, Any]


@router.get("/providers")
async def get_llm_providers():
    """Get list of available LLM providers"""
    return {"providers": get_available_providers()}


@router.post("/test")
async def check_llm_connection(
    request: LLMTestRequest,
    current_user: dict = Depends(get_current_user)
):
    """Test LLM connection before saving"""
    try:
        # Use the updated test function that handles direct client calls
        from app.services.llm_settings_service import check_llm_connection
        result = await check_llm_connection(request.provider, request.api_key)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/settings", response_model=dict)
async def save_llm_settings(
    request: LLMSettingsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save user's LLM provider and API key settings"""
    # Get model name for provider
    providers = get_available_providers()
    model = next((p["model"] for p in providers if p["value"] == request.provider), "")
    
    # Save to database
    success = await save_user_llm_settings(
        current_user["id"], 
        request.provider, 
        model, 
        request.api_key
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save settings")
    
    return {
        "message": "Settings saved successfully",
        "provider": request.provider,
        "model": model
    }


@router.get("/settings", response_model=dict)
async def get_llm_settings(
    current_user: dict = Depends(get_current_user)
):
    """Get user's current LLM settings"""
    settings = await get_user_llm_settings(current_user["id"])
    
    if not settings:
        # No settings saved yet
        return {
            "provider": "",
            "model": "",
            "has_api_key": False,
            "settings": {}
        }
    
    # Get the first (and only) provider from settings
    provider_name = list(settings.keys())[0]
    provider_config = settings[provider_name]
    
    return {
        "provider": provider_name,
        "model": provider_config.get("model", ""),
        "has_api_key": provider_config.get("has_api_key", False),
        "settings": settings
    }
