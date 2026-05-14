"""
Enhanced Sentiment Analysis Service

Provides institutional-grade sentiment analysis by:
1. Analyzing headline sentiment (VADER)
2. Detecting event types (earnings, M&A, regulatory, etc.)
3. Assessing sentiment consistency (agreement across sources)
4. Weighting by recency and source credibility
5. Integrating with macro sentiment

This replaces the basic sentiment_service.py for more nuanced analysis.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.services.news_aggregator_service import NewsAggregator

_analyzer = SentimentIntensityAnalyzer()
_news_agg = NewsAggregator()


# Event type detection patterns
EVENT_PATTERNS = {
    "earnings": r"(earnings|earnings report|Q\d|quarterly|annual report|guidance)",
    "acquisition": r"(acquisition|acquired|acquires|deal|merger|merge)",
    "regulatory": r"(SEC|FDA|regulatory|approval|lawsuit|investigation|fine|penalty)",
    "product": r"(product launch|new product|announcement|unveil|introduce|launches)",
    "partnership": r"(partners|partnership|collaboration|joint venture|alliance)",
    "dividend": r"(dividend|buyback|share repurchase)",
    "analyst": r"(analyst|rating|upgrade|downgrade|target price)",
    "macro": r"(interest rate|fed|inflation|recession|economic|gdp)",
}

# Source credibility weights (higher = more credible)
SOURCE_CREDIBILITY = {
    "Reuters": 0.95,
    "Bloomberg": 0.95,
    "AP": 0.90,
    "CNBC": 0.85,
    "MarketWatch": 0.80,
    "Seeking Alpha": 0.70,
    "Yahoo Finance": 0.75,
    "Alpha Vantage": 0.70,
    "NewsAPI": 0.65,
}


def _detect_event_type(headline: str) -> str | None:
    """Detect event type from headline"""
    headline_lower = headline.lower()

    for event_type, pattern in EVENT_PATTERNS.items():
        if re.search(pattern, headline_lower, re.IGNORECASE):
            return event_type

    return None


def _get_source_credibility(source: str) -> float:
    """Get credibility weight for source"""
    for known_source, weight in SOURCE_CREDIBILITY.items():
        if known_source.lower() in source.lower():
            return weight
    return 0.60  # Default for unknown sources


def _calculate_recency_weight(published_at: str) -> float:
    """
    Calculate recency weight (0.5-1.0).

    Recent news (< 1 day): 1.0
    1-7 days: 0.8
    7-30 days: 0.6
    > 30 days: 0.5
    """
    try:
        # Try to parse ISO format
        if "T" in published_at:
            pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        else:
            # Try other formats
            pub_date = datetime.strptime(published_at[:10], "%Y-%m-%d")

        age_days = (datetime.now() - pub_date.replace(tzinfo=None)).days

        if age_days < 1:
            return 1.0
        elif age_days < 7:
            return 0.8
        elif age_days < 30:
            return 0.6
        else:
            return 0.5
    except Exception:
        return 0.7  # Default if parsing fails


async def analyze_headline_sentiment_enhanced(ticker: str) -> dict[str, Any]:
    """
    Enhanced sentiment analysis with event detection and weighting.

    Returns:
    {
        "compound": float (-1 to 1),
        "label": "positive" | "negative" | "neutral",
        "headlines_used": int,
        "event_types": [str],
        "sentiment_consistency": float (0-1),
        "weighted_sentiment": float (-1 to 1),
        "recent_events": [str],
        "sentiment_interpretation": str,
    }
    """
    try:
        # Get news from aggregator
        news = await _news_agg.get_ticker_news(ticker, limit=10)

        if not news:
            return {
                "compound": 0.0,
                "label": "neutral",
                "headlines_used": 0,
                "event_types": [],
                "sentiment_consistency": 0.0,
                "weighted_sentiment": 0.0,
                "recent_events": [],
                "sentiment_interpretation": "No recent headlines available.",
            }

        # Analyze each headline
        sentiments = []
        event_types = set()
        recent_events = []
        weighted_scores = []

        for article in news:
            headline = article.get("title", "")
            source = article.get("source", "Unknown")
            published_at = article.get("published_at", "")

            # Get sentiment
            vader_scores = _analyzer.polarity_scores(headline)
            compound = vader_scores["compound"]
            sentiments.append(compound)

            # Detect event type
            event = _detect_event_type(headline)
            if event:
                event_types.add(event)
                recent_events.append(f"{event}: {headline[:80]}")

            # Calculate weighted score
            source_weight = _get_source_credibility(source)
            recency_weight = _calculate_recency_weight(published_at)
            weighted_score = compound * source_weight * recency_weight
            weighted_scores.append(weighted_score)

        # Calculate aggregate metrics
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        weighted_sentiment = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0

        # Sentiment consistency (agreement across sources)
        positive_count = sum(1 for s in sentiments if s > 0.15)
        negative_count = sum(1 for s in sentiments if s < -0.15)
        neutral_count = len(sentiments) - positive_count - negative_count
        consistency = max(positive_count, negative_count, neutral_count) / len(sentiments) if sentiments else 0.0

        # Determine label
        if weighted_sentiment >= 0.15:
            label = "positive"
        elif weighted_sentiment <= -0.15:
            label = "negative"
        else:
            label = "neutral"

        # Generate interpretation
        interpretation = _interpret_sentiment(
            label,
            consistency,
            list(event_types),
            len(sentiments),
        )

        return {
            "compound": round(avg_sentiment, 4),
            "label": label,
            "headlines_used": len(sentiments),
            "event_types": sorted(list(event_types)),
            "sentiment_consistency": round(consistency, 2),
            "weighted_sentiment": round(weighted_sentiment, 4),
            "recent_events": recent_events[:3],  # Top 3 recent events
            "sentiment_interpretation": interpretation,
        }
    except Exception as e:
        from loguru import logger

        logger.error(f"Enhanced sentiment analysis failed for {ticker}: {e}")
        return {
            "compound": 0.0,
            "label": "neutral",
            "headlines_used": 0,
            "event_types": [],
            "sentiment_consistency": 0.0,
            "weighted_sentiment": 0.0,
            "recent_events": [],
            "sentiment_interpretation": f"Sentiment analysis error: {str(e)[:100]}",
        }


def _interpret_sentiment(
    label: str,
    consistency: float,
    event_types: list[str],
    headline_count: int,
) -> str:
    """Generate human-readable sentiment interpretation"""
    parts = []

    # Base sentiment
    if label == "positive":
        parts.append("Positive sentiment")
    elif label == "negative":
        parts.append("Negative sentiment")
    else:
        parts.append("Neutral sentiment")

    # Consistency
    if consistency >= 0.75:
        parts.append("(strong agreement across sources)")
    elif consistency >= 0.60:
        parts.append("(moderate agreement)")
    else:
        parts.append("(mixed signals)")

    # Event context
    if event_types:
        event_str = ", ".join(event_types)
        parts.append(f"Recent events: {event_str}")

    # Data quality
    if headline_count >= 5:
        parts.append(f"({headline_count} sources)")
    elif headline_count > 0:
        parts.append(f"({headline_count} source(s), limited data)")

    return "; ".join(parts)


async def get_sentiment_with_macro_context(
    ticker: str,
    macro_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Get sentiment analysis with macro context adjustment.

    In risk-off environments, negative sentiment is amplified.
    In risk-on environments, positive sentiment is amplified.
    """
    sentiment = await analyze_headline_sentiment_enhanced(ticker)

    if not macro_context:
        return sentiment

    # Adjust sentiment based on macro environment
    risk_sentiment = macro_context.get("risk_sentiment", "risk_neutral")

    if risk_sentiment == "risk_off":
        # In risk-off, amplify negative sentiment
        if sentiment["label"] == "negative":
            sentiment["macro_adjusted_label"] = "very_negative"
            sentiment["macro_adjustment"] = "Amplified by risk-off environment"
        else:
            sentiment["macro_adjusted_label"] = sentiment["label"]
            sentiment["macro_adjustment"] = "Neutral macro context"
    elif risk_sentiment == "risk_on":
        # In risk-on, amplify positive sentiment
        if sentiment["label"] == "positive":
            sentiment["macro_adjusted_label"] = "very_positive"
            sentiment["macro_adjustment"] = "Amplified by risk-on environment"
        else:
            sentiment["macro_adjusted_label"] = sentiment["label"]
            sentiment["macro_adjustment"] = "Neutral macro context"
    else:
        sentiment["macro_adjusted_label"] = sentiment["label"]
        sentiment["macro_adjustment"] = "Neutral macro context"

    return sentiment
