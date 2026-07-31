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


async def analyze_headline_sentiment_enhanced(ticker: str, llm_settings: dict[str, Any] | None = None) -> dict[str, Any]:
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
        "news_summary": str,
        "key_headlines": [
            {
                "headline": str,
                "source": str,
                "url": str,
                "sentiment": str,
                "published_at": str
            }
        ],
        "event_analysis": {
            "total_events": int,
            "positive_events": int,
            "negative_events": int,
            "primary_catalyst": str,
            "risk_events": [str],
            "opportunity_events": [str],
            "event_driven_return": float,
        }
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
                "news_summary": "Insufficient data for sentiment analysis.",
                "key_headlines": [],
            }

        # Analyze each headline
        sentiments = []
        event_types = set()
        recent_events = []
        weighted_scores = []
        headline_details = []

        for article in news:
            headline = article.get("title", "")
            source = article.get("source", "Unknown")
            published_at = article.get("published_at", "")
            url = article.get("url", "")

            # Get sentiment
            vader_scores = _analyzer.polarity_scores(headline)
            compound = vader_scores["compound"]
            sentiments.append(compound)

            # Determine sentiment label for this headline
            if compound >= 0.15:
                headline_sentiment = "positive"
            elif compound <= -0.15:
                headline_sentiment = "negative"
            else:
                headline_sentiment = "neutral"

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

            # Store headline details for output
            headline_details.append({
                "headline": headline,
                "source": source,
                "url": url,
                "sentiment": headline_sentiment,
                "published_at": published_at,
                "compound": compound,
            })

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

        # Generate news summary (AI-synthesized from all headlines)
        news_summary = await _generate_ai_news_summary(
            ticker,
            headline_details,
            llm_settings,
        )

        # Get top 3 headlines (sorted by recency and sentiment strength)
        key_headlines = sorted(
            headline_details,
            key=lambda x: (abs(x["compound"]), x["published_at"]),
            reverse=True
        )[:3]

        # Perform event-aware sentiment analysis
        from app.services.event_sentiment_agent import EventSentimentAgent
        event_analysis = EventSentimentAgent.analyze_events(ticker, headline_details)

        return {
            "compound": round(avg_sentiment, 4),
            "label": label,
            "headlines_used": len(sentiments),
            "event_types": sorted(list(event_types)),
            "sentiment_consistency": round(consistency, 2),
            "weighted_sentiment": round(weighted_sentiment, 4),
            "recent_events": recent_events[:3],
            "sentiment_interpretation": interpretation,
            "news_summary": news_summary,
            "key_headlines": key_headlines,
            "event_analysis": event_analysis.get("event_summary", {}),
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
            "news_summary": "Error analyzing sentiment.",
            "key_headlines": [],
            "event_analysis": {
                "total_events": 0,
                "positive_events": 0,
                "negative_events": 0,
                "net_event_impact": 0.0,
                "primary_catalyst": None,
                "risk_events": [],
                "opportunity_events": [],
            },
        }


async def _generate_ai_news_summary(
    ticker: str,
    headline_details: list[dict[str, Any]],
    llm_settings: dict[str, Any] | None = None,
) -> str:
    """
    Generate AI-synthesized summary of all headlines.
    
    Summarizes the key themes, events, and sentiment drivers from all headlines.
    """
    if not headline_details:
        return "No headlines available for summary."
    
    try:
        # Prepare headlines for summarization
        headlines_text = "\n".join([
            f"- {h['headline']} ({h['source']})"
            for h in headline_details
        ])
        
        # Create summarization prompt
        prompt = f"""Analyze these {len(headline_details)} recent headlines about {ticker} and provide a concise 2-3 sentence summary of the key themes, events, and market sentiment drivers.

Headlines:
{headlines_text}

Summary (2-3 sentences, focus on key themes and sentiment drivers):"""
        
        # Use LLM to generate summary
        from app.services.llm_service import generate_with_provider, LLMProvider
        
        # Get LLM settings from parameter or use defaults
        if not llm_settings or not llm_settings.get("provider"):
            return _fallback_summary(headline_details)
        
        provider = LLMProvider(llm_settings["provider"])
        api_key = llm_settings.get("api_key")
        
        summary = await generate_with_provider(
            provider=provider,
            prompt=prompt,
            api_key=api_key,
            temperature=0.4,
            max_tokens=150
        )
        return summary.strip() if summary else _fallback_summary(headline_details)
    
    except Exception as e:
        from loguru import logger
        logger.warning(f"AI summary generation failed for {ticker}: {e}")
        return _fallback_summary(headline_details)


def _fallback_summary(headline_details: list[dict[str, Any]]) -> str:
    """Fallback summary if AI generation fails"""
    if not headline_details:
        return "No headlines available."
    
    # Extract key themes from headlines
    themes = set()
    for h in headline_details:
        headline_lower = h["headline"].lower()
        if "earnings" in headline_lower:
            themes.add("earnings")
        if "analyst" in headline_lower or "upgrade" in headline_lower or "downgrade" in headline_lower:
            themes.add("analyst activity")
        if "acquisition" in headline_lower or "merger" in headline_lower:
            themes.add("M&A activity")
        if "product" in headline_lower or "launch" in headline_lower:
            themes.add("product news")
        if "regulatory" in headline_lower or "sec" in headline_lower:
            themes.add("regulatory matters")
    
    # Count sentiment
    positive = sum(1 for h in headline_details if h["sentiment"] == "positive")
    negative = sum(1 for h in headline_details if h["sentiment"] == "negative")
    
    # Build fallback summary
    theme_str = ", ".join(sorted(themes)) if themes else "mixed developments"
    sentiment_str = "positive" if positive > negative else "negative" if negative > positive else "mixed"
    
    return f"Recent news shows {sentiment_str} sentiment with focus on {theme_str}. Based on {len(headline_details)} headlines from multiple sources."


def _interpret_sentiment(
    label: str,
    consistency: float,
    event_types: list[str],
    headlines_count: int,
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
    if headlines_count >= 5:
        parts.append(f"({headlines_count} sources)")
    elif headlines_count > 0:
        parts.append(f"({headlines_count} source(s), limited data)")

    return "; ".join(parts)


async def get_sentiment_with_macro_context(
    ticker: str,
    macro_context: dict[str, Any] | None = None,
    llm_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Get sentiment analysis with macro context adjustment.

    In risk-off environments, negative sentiment is amplified.
    In risk-on environments, positive sentiment is amplified.
    """
    sentiment = await analyze_headline_sentiment_enhanced(ticker, llm_settings)

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
