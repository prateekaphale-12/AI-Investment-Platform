from __future__ import annotations

from typing import Any

from app.services.narrative_builder import (
    build_fundamental_narrative,
    build_risk_narrative,
    build_sentiment_narrative,
    build_technical_narrative,
)


def describe_market_trend(market: dict[str, Any]) -> str:
    ytd = market.get("ytd_return_pct")
    price = market.get("current_price")
    if ytd is None:
        return "Insufficient price history for trend summary."
    direction = "up" if ytd >= 0 else "down"
    # Format price to 2 decimal places
    formatted_price = f"{price:.2f}" if price is not None else "N/A"
    return f"Trailing period return ~{ytd}% ({direction}); last price {formatted_price}."


def describe_technical(tech: dict[str, Any]) -> str:
    """
    Provide institutional-grade technical narrative.
    
    Uses narrative_builder to convert internal signals into premium language.
    """
    return build_technical_narrative(tech)


def describe_sentiment(sent: dict[str, Any]) -> str:
    """
    Provide institutional-grade sentiment narrative with AI-synthesized news summary.
    
    Format:
    Sentiment: [Label]
    
    Summary based on news:
    [AI-synthesized summary of all headlines]
    
    Key Headlines:
    - [Headline 1] (Source) ↗
    - [Headline 2] (Source) ↗
    - [Headline 3] (Source) ↗
    """
    label = sent.get("label", "neutral").capitalize()
    news_summary = sent.get("news_summary", "")
    key_headlines = sent.get("key_headlines", [])
    
    parts = [f"Sentiment: {label}\n"]
    
    if news_summary:
        parts.append(f"Summary based on news:\n{news_summary}\n")
    
    if key_headlines:
        parts.append("Key Headlines:")
        for headline in key_headlines:
            title = headline.get("headline", "")
            source = headline.get("source", "Unknown")
            url = headline.get("url", "")
            
            # Truncate long headlines
            if len(title) > 80:
                title = title[:77] + "..."
            
            if url:
                parts.append(f"  • {title}")
                parts.append(f"    Source: {source} | {url}")
            else:
                parts.append(f"  • {title} ({source})")
    
    return "\n".join(parts)


def describe_fundamentals(info: dict[str, Any]) -> str:
    """
    Provide institutional-grade fundamental narrative.
    
    Uses narrative_builder to convert fundamental data into premium language.
    """
    return build_fundamental_narrative(info)


def describe_risk(info: dict[str, Any], tech: dict[str, Any]) -> str:
    """
    Provide institutional-grade risk narrative.
    
    Uses narrative_builder to convert risk factors into premium language.
    """
    confidence = tech.get("confidence", 0.0)
    return build_risk_narrative(info, tech, confidence)


def describe_confidence(confidence_data: dict[str, Any]) -> str:
    """
    Describe multi-factor confidence breakdown.
    
    Shows how technical, fundamental, sentiment, and macro factors
    combine to create final confidence score.
    """
    if not confidence_data:
        return "Confidence analysis unavailable."
    
    final = confidence_data.get("final_confidence", 0.0)
    label = confidence_data.get("confidence_label", "unknown")
    components = confidence_data.get("components", {})
    
    if not components:
        return f"Overall confidence: {label} ({round(final * 100)}%)"
    
    parts = [f"Overall confidence: {label} ({round(final * 100)}%)"]
    
    # Component breakdown
    tech = components.get("technical", 0.0)
    fund = components.get("fundamental", 0.0)
    sent = components.get("sentiment", 0.0)
    macro = components.get("macro", 0.0)
    
    parts.append(f"Technical: {round(tech * 100)}%")
    parts.append(f"Fundamental: {round(fund * 100)}%")
    parts.append(f"Sentiment: {round(sent * 100)}%")
    parts.append(f"Macro: {round(macro * 100)}%")
    
    # Confidence interpretation
    if final >= 0.7:
        parts.append("(High confidence: multiple factors aligned)")
    elif final >= 0.55:
        parts.append("(Moderate confidence: mixed signals)")
    else:
        parts.append("(Low confidence: weak or conflicting signals)")
    
    return "; ".join(parts)
