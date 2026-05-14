from __future__ import annotations

import asyncio
import json
from enum import Enum
from typing import Any, Dict, Literal

from groq import AsyncGroq
from loguru import logger
from openai import AsyncOpenAI

from app.config import settings


class LLMProvider(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"


class LLMConfig:
    def __init__(self, provider: LLMProvider, api_key: str, model: str):
        self.provider = provider
        self.api_key = api_key
        self.model = model


def get_llm_config(provider: LLMProvider, api_key: str = None) -> LLMConfig:
    """Get LLM config for a specific provider"""
    if provider == LLMProvider.OPENAI:
        return LLMConfig(
            provider=provider,
            api_key=api_key or settings.openai_api_key,
            model=settings.openai_model
        )
    elif provider == LLMProvider.GROQ:
        return LLMConfig(
            provider=provider,
            api_key=api_key or settings.groq_api_key,
            model=settings.groq_model
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")




async def _generate_with_openai(config: LLMConfig, prompt: str, temperature: float = 0.4, max_tokens: int = 8192) -> str:
    """Generate text using OpenAI"""
    if not config.api_key:
        raise ValueError("OpenAI API key is required")
    
    client = AsyncOpenAI(api_key=config.api_key)
    response = await client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content or ""


async def _generate_with_groq(config: LLMConfig, prompt: str, temperature: float = 0.4, max_tokens: int = 8192) -> str:
    """Generate text using Groq"""
    if not config.api_key:
        raise ValueError("Groq API key is required")
    
    client = AsyncGroq(api_key=config.api_key)
    response = await client.chat.completions.create(
        model=config.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content or ""


async def generate_with_provider(
    provider: LLMProvider, 
    prompt: str, 
    api_key: str = None,
    temperature: float = 0.4, 
    max_tokens: int = 8192
) -> str:
    """Generate text using specified provider"""
    config = get_llm_config(provider, api_key)
    
    if not config.api_key:
        raise ValueError(f"API key is required for {provider.value}")
    
    try:
        if provider == LLMProvider.OPENAI:
            return await _generate_with_openai(config, prompt, temperature, max_tokens)
        elif provider == LLMProvider.GROQ:
            return await _generate_with_groq(config, prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        logger.error(f"LLM generation failed with {provider}: {e}")
        raise


async def generate_investment_report(
    prompt: str, 
    provider: LLMProvider = LLMProvider.GROQ,
    api_key: str = None
) -> str:
    """Generate investment report using specified provider"""
    try:
        # Reduce max_tokens to stay within Groq free tier (6000 TPM limit)
        # With prompt + response, keep total under 5000 tokens
        return await generate_with_provider(provider, prompt, api_key, temperature=0.4, max_tokens=2048)
    except Exception as e:
        logger.exception(f"Investment report generation failed with {provider}: {e}")
        return f"## Report generation error\n\n{e!s}\n\n---\n\n{prompt[:2000]}"


async def generate_ticker_summaries(
    prompt: str, 
    provider: LLMProvider = LLMProvider.GROQ,
    api_key: str = None
) -> str:
    """Generate ticker summaries using specified provider"""
    try:
        # Reduce max_tokens to stay within Groq free tier
        return await generate_with_provider(provider, prompt, api_key, temperature=0.35, max_tokens=1024)
    except Exception as e:
        logger.exception(f"Ticker summaries failed with {provider}: {e}")
        return ""


async def generate_json_object(
    prompt: str, 
    provider: LLMProvider = LLMProvider.GROQ,
    api_key: str = None,
    max_tokens: int = 2048
) -> Dict[str, Any]:
    """Generate JSON object using specified provider"""
    config = get_llm_config(provider, api_key)
    
    if not config.api_key:
        return {}
    
    wrapped = (
        "Return ONLY valid JSON object. No markdown, no prose.\n"
        "If uncertain, return minimal object with available fields.\n\n"
        + prompt
    )
    
    try:
        if provider == LLMProvider.OPENAI:
            text = await _generate_with_openai(config, wrapped, temperature=0.2, max_tokens=max_tokens)
        elif provider == LLMProvider.GROQ:
            text = await _generate_with_groq(config, wrapped, temperature=0.2, max_tokens=max_tokens)
        else:
            return {}
        
        if not text:
            return {}
        
        start = text.find("{")
        end = text.rfind("}")
        raw = text[start : end + 1] if start != -1 and end != -1 and end >= start else text
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning(f"JSON generation failed with {provider}: {e}")
        return {}


def get_available_providers() -> list[Dict[str, str]]:
    """Get list of available LLM providers"""
    return [
        {"value": LLMProvider.OPENAI.value, "label": "OpenAI GPT", "model": settings.openai_model},
        {"value": LLMProvider.GROQ.value, "label": "Groq (Llama)", "model": settings.groq_model},
    ]
