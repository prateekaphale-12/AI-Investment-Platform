from __future__ import annotations

import asyncio
import json

from google import genai as google_genai
from google.genai import types as genai_types
from loguru import logger

from app.config import settings


def _client_configured() -> bool:
    return bool(settings.gemini_api_key)


def _extract_text(resp: object) -> str:
    t = getattr(resp, "text", None)
    if t:
        return str(t).strip()
    candidates = getattr(resp, "candidates", None) or []
    parts_out: list[str] = []
    for c in candidates:
        content = getattr(c, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", None) or []:
            tx = getattr(part, "text", None)
            if tx:
                parts_out.append(str(tx))
    return "\n".join(parts_out).strip()


def _gen_sync(prompt: str, *, temperature: float, max_tokens: int) -> str:
    client = google_genai.Client(api_key=settings.gemini_api_key)
    resp = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return _extract_text(resp)


async def generate_investment_report(markdown_prompt: str) -> str:
    if not _client_configured():
        logger.warning("GEMINI_API_KEY missing; returning placeholder report")
        return (
            "## Investment research report\n\n"
            "_Configure `GEMINI_API_KEY` for AI-generated narrative._\n\n"
            + markdown_prompt[:4000]
        )
    try:
        text = await asyncio.to_thread(
            _gen_sync,
            markdown_prompt,
            temperature=0.4,
            max_tokens=8192,
        )
        return text or "## Report\n\n_No content returned._"
    except Exception as e:
        logger.exception("Gemini report failed: {}", e)
        return f"## Report generation error\n\n{e!s}\n\n---\n\n{markdown_prompt[:2000]}"


async def generate_ticker_summaries(batch_prompt: str) -> str:
    """Returns model text; caller parses JSON or lines if needed."""
    if not _client_configured():
        return ""
    try:
        return await asyncio.to_thread(
            _gen_sync,
            batch_prompt,
            temperature=0.35,
            max_tokens=4096,
        )
    except Exception as e:
        logger.exception("Gemini summaries failed: {}", e)
        return ""


async def generate_json_object(prompt: str, *, max_tokens: int = 2048) -> dict:
    """
    Ask Gemini for a JSON object and parse it safely.
    Returns {} on any failure.
    """
    if not _client_configured():
        return {}
    wrapped = (
        "Return ONLY valid JSON object. No markdown, no prose.\n"
        "If uncertain, return minimal object with available fields.\n\n"
        + prompt
    )
    try:
        text = await asyncio.to_thread(_gen_sync, wrapped, temperature=0.2, max_tokens=max_tokens)
        if not text:
            return {}
        start = text.find("{")
        end = text.rfind("}")
        raw = text[start : end + 1] if start != -1 and end != -1 and end >= start else text
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning("Gemini JSON parse failed: {}", e)
        return {}
