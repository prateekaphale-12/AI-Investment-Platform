from __future__ import annotations

import asyncio
from typing import Any

import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def _headlines_sync(ticker: str) -> list[str]:
    t = yf.Ticker(ticker)
    try:
        news = t.news or []
        return [str(n.get("title", "")) for n in news if n.get("title")]
    except Exception:
        return []


async def analyze_headline_sentiment(ticker: str) -> dict[str, Any]:
    headlines = await asyncio.to_thread(_headlines_sync, ticker)
    if not headlines:
        return {"compound": 0.0, "label": "neutral", "headlines_used": 0}
    scores = [_analyzer.polarity_scores(h)["compound"] for h in headlines]
    avg = sum(scores) / len(scores)
    label = "positive" if avg >= 0.15 else "negative" if avg <= -0.15 else "neutral"
    return {"compound": round(avg, 4), "label": label, "headlines_used": len(headlines)}
