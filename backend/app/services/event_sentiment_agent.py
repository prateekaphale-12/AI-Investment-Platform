"""
Event-Aware Sentiment Agent

Enhances sentiment analysis by:
1. Detecting event types (earnings, M&A, regulatory, product, etc.)
2. Assessing event impact (positive/negative/neutral)
3. Estimating event probability and timing
4. Calculating event-driven return expectations
5. Identifying catalysts and risks

This agent moves beyond simple headline sentiment to understand:
- What events are driving sentiment
- How material each event is
- When the event might impact the stock
- What the market is pricing in

OUTPUT:
{
    "ticker": "AAPL",
    "events": [
        {
            "type": "earnings",
            "headline": "Apple Q4 earnings beat expectations",
            "impact": "positive",
            "materiality": 0.85,
            "timing": "immediate",
            "probability": 0.95,
            "expected_move": 3.5,
            "source": "Reuters",
            "published_at": "2024-01-15T10:30:00Z"
        },
        {
            "type": "regulatory",
            "headline": "EU antitrust investigation into App Store practices",
            "impact": "negative",
            "materiality": 0.65,
            "timing": "medium_term",
            "probability": 0.70,
            "expected_move": -2.5,
            "source": "Bloomberg",
            "published_at": "2024-01-14T15:00:00Z"
        }
    ],
    "event_summary": {
        "total_events": 2,
        "positive_events": 1,
        "negative_events": 1,
        "net_event_impact": 1.0,
        "primary_catalyst": "earnings",
        "risk_events": ["regulatory"],
        "opportunity_events": ["earnings"],
    },
    "event_driven_return": 2.5,
    "event_driven_volatility": 4.2,
    "sentiment_with_events": "positive",
    "confidence_in_sentiment": 0.78,
}
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

# Event type patterns and materiality scores
EVENT_DEFINITIONS = {
    "earnings": {
        "patterns": r"(earnings|earnings report|Q\d|quarterly|annual report|guidance|EPS|revenue beat|miss)",
        "base_materiality": 0.90,
        "impact_keywords": {
            "beat": 0.8,
            "miss": -0.8,
            "raise": 0.7,
            "lower": -0.7,
            "strong": 0.6,
            "weak": -0.6,
        }
    },
    "acquisition": {
        "patterns": r"(acquisition|acquired|acquires|deal|merger|merge|buyout|takeover)",
        "base_materiality": 0.85,
        "impact_keywords": {
            "acquire": 0.5,
            "acquired": 0.5,
            "deal": 0.4,
            "premium": 0.3,
        }
    },
    "regulatory": {
        "patterns": r"(SEC|FDA|regulatory|approval|lawsuit|investigation|fine|penalty|antitrust|compliance)",
        "base_materiality": 0.75,
        "impact_keywords": {
            "approval": 0.7,
            "approved": 0.7,
            "investigation": -0.6,
            "lawsuit": -0.5,
            "fine": -0.7,
            "penalty": -0.6,
        }
    },
    "product": {
        "patterns": r"(product launch|new product|announcement|unveil|introduce|launches|release|beta)",
        "base_materiality": 0.70,
        "impact_keywords": {
            "launch": 0.5,
            "new": 0.4,
            "revolutionary": 0.6,
            "innovative": 0.5,
            "delay": -0.5,
            "cancel": -0.7,
        }
    },
    "partnership": {
        "patterns": r"(partners|partnership|collaboration|joint venture|alliance|strategic|deal)",
        "base_materiality": 0.65,
        "impact_keywords": {
            "partnership": 0.4,
            "collaboration": 0.4,
            "strategic": 0.3,
            "exclusive": 0.5,
        }
    },
    "dividend": {
        "patterns": r"(dividend|buyback|share repurchase|capital return|shareholder)",
        "base_materiality": 0.60,
        "impact_keywords": {
            "increase": 0.4,
            "raise": 0.4,
            "buyback": 0.3,
            "suspend": -0.5,
        }
    },
    "analyst": {
        "patterns": r"(analyst|rating|upgrade|downgrade|target price|price target|initiate)",
        "base_materiality": 0.55,
        "impact_keywords": {
            "upgrade": 0.6,
            "downgrade": -0.6,
            "outperform": 0.5,
            "underperform": -0.5,
            "buy": 0.4,
            "sell": -0.4,
        }
    },
    "macro": {
        "patterns": r"(interest rate|fed|inflation|recession|economic|gdp|employment|trade)",
        "base_materiality": 0.50,
        "impact_keywords": {
            "rate hike": -0.4,
            "rate cut": 0.4,
            "inflation": -0.3,
            "recession": -0.5,
        }
    },
}

# Timing categories
TIMING_CATEGORIES = {
    "immediate": {"days": 0, "description": "Already happened or happening now"},
    "short_term": {"days": 7, "description": "Within 1 week"},
    "medium_term": {"days": 30, "description": "Within 1 month"},
    "long_term": {"days": 90, "description": "Within 3 months"},
}


class EventSentimentAgent:
    """Analyzes sentiment with event-aware context."""
    
    @staticmethod
    def detect_event_type(headline: str) -> str | None:
        """Detect event type from headline."""
        headline_lower = headline.lower()
        
        for event_type, definition in EVENT_DEFINITIONS.items():
            if re.search(definition["patterns"], headline_lower, re.IGNORECASE):
                return event_type
        
        return None
    
    @staticmethod
    def assess_event_impact(headline: str, event_type: str) -> float:
        """
        Assess event impact (-1.0 to 1.0).
        
        Positive = bullish, Negative = bearish
        """
        headline_lower = headline.lower()
        definition = EVENT_DEFINITIONS.get(event_type, {})
        impact_keywords = definition.get("impact_keywords", {})
        
        # Find matching keywords
        max_impact = 0.0
        for keyword, impact_value in impact_keywords.items():
            if keyword.lower() in headline_lower:
                max_impact = max(abs(max_impact), abs(impact_value)) * (1 if impact_value > 0 else -1)
        
        # If no keywords found, use neutral impact
        if max_impact == 0.0:
            max_impact = 0.2 if "positive" in headline_lower or "strong" in headline_lower else (
                -0.2 if "negative" in headline_lower or "weak" in headline_lower else 0.0
            )
        
        return max(- 1.0, min(1.0, max_impact))
    
    @staticmethod
    def calculate_materiality(
        event_type: str,
        headline: str,
        source_credibility: float = 0.75,
    ) -> float:
        """
        Calculate event materiality (0-1).
        
        Materiality = how much this event should move the stock.
        """
        definition = EVENT_DEFINITIONS.get(event_type, {})
        base_materiality = definition.get("base_materiality", 0.50)
        
        # Adjust for source credibility
        materiality = base_materiality * source_credibility
        
        # Adjust for headline length (longer = more detailed = more material)
        headline_length = len(headline.split())
        if headline_length > 15:
            materiality *= 1.1
        elif headline_length < 5:
            materiality *= 0.9
        
        return max(0.0, min(1.0, materiality))
    
    @staticmethod
    def estimate_timing(published_at: str) -> str:
        """Estimate timing category based on publication date."""
        try:
            if "T" in published_at:
                pub_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            else:
                pub_date = datetime.strptime(published_at[:10], "%Y-%m-%d")
            
            age_days = (datetime.now() - pub_date.replace(tzinfo=None)).days
            
            if age_days <= 0:
                return "immediate"
            elif age_days <= 7:
                return "short_term"
            elif age_days <= 30:
                return "medium_term"
            else:
                return "long_term"
        except Exception:
            return "medium_term"
    
    @staticmethod
    def estimate_event_probability(event_type: str, headline: str) -> float:
        """
        Estimate probability that event will impact stock.
        
        Some events are certain (earnings already happened),
        others are speculative (potential acquisition).
        """
        headline_lower = headline.lower()
        
        # Certain events (already happened)
        if any(word in headline_lower for word in ["reported", "announced", "released", "beat", "missed"]):
            return 0.95
        
        # Likely events (strong signals)
        if any(word in headline_lower for word in ["approved", "approved", "confirmed", "official"]):
            return 0.85
        
        # Speculative events (potential, rumored)
        if any(word in headline_lower for word in ["potential", "rumored", "could", "may", "might", "expected"]):
            return 0.60
        
        # Default
        return 0.70
    
    @staticmethod
    def estimate_expected_move(
        event_type: str,
        impact: float,
        materiality: float,
        probability: float,
    ) -> float:
        """
        Estimate expected stock price move (in %).
        
        Formula: impact * materiality * probability * event_volatility
        """
        # Base event volatility by type
        event_volatility = {
            "earnings": 4.0,
            "acquisition": 5.0,
            "regulatory": 3.5,
            "product": 2.5,
            "partnership": 1.5,
            "dividend": 1.0,
            "analyst": 1.5,
            "macro": 2.0,
        }
        
        base_vol = event_volatility.get(event_type, 2.0)
        
        # Calculate expected move
        expected_move = impact * materiality * probability * base_vol
        
        return round(expected_move, 2)
    
    @staticmethod
    def analyze_events(
        ticker: str,
        headlines: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Analyze all headlines for events and their impact.
        
        Returns: comprehensive event analysis
        """
        if not headlines:
            return {
                "ticker": ticker,
                "events": [],
                "event_summary": {
                    "total_events": 0,
                    "positive_events": 0,
                    "negative_events": 0,
                    "net_event_impact": 0.0,
                    "primary_catalyst": None,
                    "risk_events": [],
                    "opportunity_events": [],
                },
                "event_driven_return": 0.0,
                "event_driven_volatility": 0.0,
            }
        
        events = []
        positive_count = 0
        negative_count = 0
        total_impact = 0.0
        total_volatility = 0.0
        
        for headline_data in headlines:
            headline = headline_data.get("headline", "")
            source = headline_data.get("source", "Unknown")
            published_at = headline_data.get("published_at", "")
            url = headline_data.get("url", "")
            
            # Detect event type
            event_type = EventSentimentAgent.detect_event_type(headline)
            if not event_type:
                continue
            
            # Assess impact
            impact = EventSentimentAgent.assess_event_impact(headline, event_type)
            
            # Calculate materiality
            source_credibility = 0.75  # Default
            materiality = EventSentimentAgent.calculate_materiality(
                event_type,
                headline,
                source_credibility
            )
            
            # Estimate timing
            timing = EventSentimentAgent.estimate_timing(published_at)
            
            # Estimate probability
            probability = EventSentimentAgent.estimate_event_probability(event_type, headline)
            
            # Estimate expected move
            expected_move = EventSentimentAgent.estimate_expected_move(
                event_type,
                impact,
                materiality,
                probability
            )
            
            # Track counts
            if impact > 0.2:
                positive_count += 1
            elif impact < -0.2:
                negative_count += 1
            
            total_impact += impact * materiality * probability
            total_volatility += abs(expected_move)
            
            events.append({
                "type": event_type,
                "headline": headline,
                "impact": round(impact, 2),
                "materiality": round(materiality, 2),
                "timing": timing,
                "probability": round(probability, 2),
                "expected_move": expected_move,
                "source": source,
                "published_at": published_at,
                "url": url,
            })
        
        # Sort by materiality (most important first)
        events = sorted(events, key=lambda x: x["materiality"], reverse=True)
        
        # Determine primary catalyst
        primary_catalyst = events[0]["type"] if events else None
        
        # Identify risk and opportunity events
        risk_events = [e["type"] for e in events if e["impact"] < -0.2]
        opportunity_events = [e["type"] for e in events if e["impact"] > 0.2]
        
        # Determine overall sentiment with events
        if total_impact > 0.3:
            sentiment_with_events = "positive"
        elif total_impact < -0.3:
            sentiment_with_events = "negative"
        else:
            sentiment_with_events = "neutral"
        
        # Confidence in sentiment (based on event clarity)
        if events:
            avg_materiality = sum(e["materiality"] for e in events) / len(events)
            confidence = min(0.95, 0.5 + avg_materiality * 0.5)
        else:
            confidence = 0.5
        
        return {
            "ticker": ticker,
            "events": events,
            "event_summary": {
                "total_events": len(events),
                "positive_events": positive_count,
                "negative_events": negative_count,
                "net_event_impact": round(total_impact, 2),
                "primary_catalyst": primary_catalyst,
                "risk_events": list(set(risk_events)),
                "opportunity_events": list(set(opportunity_events)),
            },
            "event_driven_return": round(total_impact * 100, 2),
            "event_driven_volatility": round(total_volatility, 2),
            "sentiment_with_events": sentiment_with_events,
            "confidence_in_sentiment": round(confidence, 2),
        }
    
    @staticmethod
    def generate_event_narrative(event_analysis: dict[str, Any]) -> str:
        """Generate human-readable narrative from event analysis."""
        ticker = event_analysis.get("ticker", "")
        events = event_analysis.get("events", [])
        summary = event_analysis.get("event_summary", {})
        
        if not events:
            return f"No significant events detected for {ticker}."
        
        parts = []
        
        # Summary line
        total = summary.get("total_events", 0)
        positive = summary.get("positive_events", 0)
        negative = summary.get("negative_events", 0)
        
        if positive > negative:
            tone = "positive"
        elif negative > positive:
            tone = "negative"
        else:
            tone = "mixed"
        
        parts.append(f"Event Analysis: {total} events detected ({tone} tone)")
        
        # Primary catalyst
        primary = summary.get("primary_catalyst")
        if primary:
            parts.append(f"Primary catalyst: {primary.capitalize()}")
        
        # Top events
        parts.append("\nTop Events:")
        for event in events[:3]:
            headline = event.get("headline", "")
            impact = event.get("impact", 0)
            expected_move = event.get("expected_move", 0)
            
            impact_str = "↑" if impact > 0 else "↓" if impact < 0 else "→"
            parts.append(f"  {impact_str} {headline[:80]}")
            parts.append(f"     Expected move: {expected_move:+.1f}%")
        
        # Risk events
        risk_events = summary.get("risk_events", [])
        if risk_events:
            parts.append(f"\nRisk Events: {', '.join(risk_events)}")
        
        # Opportunity events
        opp_events = summary.get("opportunity_events", [])
        if opp_events:
            parts.append(f"Opportunities: {', '.join(opp_events)}")
        
        return "\n".join(parts)
