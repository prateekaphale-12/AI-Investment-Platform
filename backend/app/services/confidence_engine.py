"""
Multi-factor confidence scoring engine.

Replaces single-factor technical confidence with institutional-grade
multi-factor confidence that combines:
- Technical signals (capped at 0.6)
- Fundamental strength (0.5-0.8)
- Sentiment alignment (0.4-0.8)
- Macro regime (0.5-0.8)

Final confidence = weighted average of all factors
"""

from __future__ import annotations

from typing import Any
from loguru import logger


def calculate_technical_confidence(tech: dict[str, Any]) -> float:
    """
    Calculate technical confidence (capped at 0.6).
    
    Technical analysis alone should never be >60% confident.
    Factors:
    - Signal agreement (trend + momentum alignment)
    - Extension state (neutral = higher confidence)
    - Long-term trend alignment
    
    EXPANDED RANGE: 0.25-0.60 (more differentiation)
    """
    if not tech or tech.get("confidence") is None:
        return 0.25
    
    signal = tech.get("signal", "neutral")
    trend = tech.get("trend", "unknown")
    momentum = tech.get("momentum", "unknown")
    extension = tech.get("extension", "unknown")
    long_term = tech.get("long_term_trend", "unknown")
    
    # Start lower for more differentiation
    base_confidence = 0.30
    
    # Signal strength (primary factor)
    if signal == "bullish":
        base_confidence = 0.50
    elif signal == "bearish":
        base_confidence = 0.35
    elif signal == "bullish_but_extended":
        base_confidence = 0.45
    elif signal == "bearish_but_oversold":
        base_confidence = 0.40
    elif signal == "mixed":
        base_confidence = 0.35
    else:  # neutral
        base_confidence = 0.30
    
    # Signal agreement boost (trend + momentum alignment)
    if trend != "unknown" and momentum != "unknown" and trend == momentum:
        base_confidence += 0.08
    elif trend != "unknown" and momentum != "unknown" and trend != momentum:
        base_confidence -= 0.05  # Conflicting signals reduce confidence
    
    # Extension state adjustment
    if extension == "neutral":
        base_confidence += 0.05
    elif "strongly_overbought" in extension or "strongly_oversold" in extension:
        base_confidence -= 0.08  # Extreme extension = lower confidence
    elif "overbought" in extension or "oversold" in extension:
        base_confidence -= 0.03
    
    # Long-term trend alignment
    if long_term != "unknown" and signal != "neutral":
        if (long_term == "bullish" and "bullish" in signal):
            base_confidence += 0.07  # Strong alignment
        elif (long_term == "bearish" and "bearish" in signal):
            base_confidence += 0.05
        elif (long_term == "bullish" and "bearish" in signal) or \
             (long_term == "bearish" and "bullish" in signal):
            base_confidence -= 0.08  # Conflicting long-term vs short-term
    
    # Cap at 0.6, floor at 0.25 (wider range for differentiation)
    return round(max(0.25, min(base_confidence, 0.6)), 2)


def calculate_fundamental_confidence(fundamentals: dict[str, Any]) -> float:
    """
    Calculate fundamental confidence (0.4-0.85).
    
    Factors:
    - P/E ratio (extreme valuations = lower confidence)
    - Revenue growth (strong growth = higher confidence)
    - Profit margin (healthy margins = higher confidence)
    - PEG ratio (reasonable PEG = higher confidence)
    
    EXPANDED RANGE: 0.4-0.85 (more differentiation)
    """
    if not fundamentals:
        return 0.45
    
    confidence = 0.50
    
    # P/E valuation check (more aggressive scoring)
    pe = fundamentals.get("trailingPE")
    if pe is not None and isinstance(pe, (int, float)):
        pe_float = float(pe)
        if 15 <= pe_float <= 25:
            confidence += 0.20  # Fair valuation (increased from 0.15)
        elif 10 <= pe_float < 15:
            confidence += 0.15  # Undervalued
        elif 25 < pe_float <= 35:
            confidence += 0.05  # Slightly expensive
        elif pe_float > 50:
            confidence -= 0.15  # Very expensive (increased penalty)
        elif pe_float > 40:
            confidence -= 0.10
    
    # Revenue growth check (more aggressive scoring)
    rg = fundamentals.get("revenueGrowth")
    if rg is not None and isinstance(rg, (int, float)):
        rg_pct = float(rg) * 100
        if rg_pct > 20:
            confidence += 0.15  # Very strong growth
        elif rg_pct > 15:
            confidence += 0.12  # Strong growth
        elif rg_pct > 10:
            confidence += 0.08
        elif rg_pct > 5:
            confidence += 0.04  # Moderate growth
        elif rg_pct < 0:
            confidence -= 0.15  # Declining revenue (increased penalty)
        elif rg_pct < 3:
            confidence -= 0.05  # Weak growth
    
    # Profit margin check (more aggressive scoring)
    pm = fundamentals.get("profitMargins")
    if pm is not None and isinstance(pm, (int, float)):
        pm_pct = float(pm) * 100
        if pm_pct > 20:
            confidence += 0.15  # Excellent margins
        elif pm_pct > 15:
            confidence += 0.10  # Healthy margins
        elif pm_pct > 10:
            confidence += 0.06
        elif pm_pct > 5:
            confidence += 0.03  # Acceptable margins
        elif pm_pct < 0:
            confidence -= 0.15  # Unprofitable (increased penalty)
        elif pm_pct < 3:
            confidence -= 0.08
    
    # PEG-like reasoning (more aggressive scoring)
    if pe is not None and rg is not None:
        pe_float = float(pe)
        rg_pct = float(rg) * 100
        if rg_pct > 0:
            peg_proxy = pe_float / rg_pct
            if peg_proxy < 1.0:
                confidence += 0.15  # Excellent value
            elif peg_proxy < 1.5:
                confidence += 0.10  # Growth justifies valuation
            elif peg_proxy > 3.0:
                confidence -= 0.15  # Expensive vs growth
            elif peg_proxy > 2.5:
                confidence -= 0.10  # Valuation premium vs growth
    
    # Clamp to 0.4-0.85 range (wider range)
    return round(max(0.40, min(confidence, 0.85)), 2)


def calculate_sentiment_confidence(sentiment: dict[str, Any]) -> float:
    """
    Calculate sentiment confidence (0.35-0.80).
    
    Factors:
    - Headline availability (no headlines = lower confidence)
    - Sentiment direction (strong positive/negative = higher confidence)
    - Sentiment consistency (aligned with technicals = higher confidence)
    - Event detection (earnings, M&A = higher confidence)
    
    EXPANDED RANGE: 0.35-0.80 (more differentiation)
    """
    if not sentiment:
        return 0.35
    
    headlines_used = sentiment.get("headlines_used", 0)
    
    # No headlines = low confidence
    if headlines_used == 0:
        return 0.35
    
    confidence = 0.45
    
    # Headline count boost (more aggressive)
    if headlines_used >= 10:
        confidence += 0.18
    elif headlines_used >= 7:
        confidence += 0.14
    elif headlines_used >= 5:
        confidence += 0.10
    elif headlines_used >= 3:
        confidence += 0.05
    else:
        confidence -= 0.05  # Very few headlines
    
    # Sentiment strength (more aggressive)
    compound = sentiment.get("compound", 0.0)
    if isinstance(compound, (int, float)):
        abs_compound = abs(float(compound))
        if abs_compound > 0.6:
            confidence += 0.20  # Very strong sentiment
        elif abs_compound > 0.5:
            confidence += 0.15  # Strong sentiment
        elif abs_compound > 0.3:
            confidence += 0.10  # Moderate sentiment
        elif abs_compound < 0.1:
            confidence -= 0.08  # Weak/mixed sentiment (increased penalty)
    
    # Sentiment consistency (if available from enhanced sentiment)
    consistency = sentiment.get("sentiment_consistency")
    if consistency is not None and isinstance(consistency, (int, float)):
        if float(consistency) > 0.8:
            confidence += 0.10  # High agreement across sources
        elif float(consistency) < 0.5:
            confidence -= 0.08  # Low agreement (conflicting signals)
    
    # Event detection boost (if available)
    event_types = sentiment.get("event_types", [])
    if event_types and len(event_types) > 0:
        confidence += 0.05  # Events detected = more reliable sentiment
    
    # Clamp to 0.35-0.80 range (wider range)
    return round(max(0.35, min(confidence, 0.80)), 2)


def calculate_macro_confidence(macro: dict[str, Any]) -> float:
    """
    Calculate macro confidence (0.5-0.8).
    
    Factors:
    - Interest rate regime (aligned with stock = higher confidence)
    - Economic growth (strong growth = higher confidence)
    - Sector rotation (aligned with sector = higher confidence)
    - Recession probability (low = higher confidence)
    
    For now, returns baseline since macro data not yet integrated.
    """
    if not macro:
        return 0.5
    
    confidence = 0.5
    
    # Interest rate regime
    rate_regime = macro.get("rate_regime")  # "rising", "falling", "stable"
    if rate_regime == "stable":
        confidence += 0.1
    elif rate_regime == "falling":
        confidence += 0.05
    elif rate_regime == "rising":
        confidence -= 0.05
    
    # Economic growth
    gdp_growth = macro.get("gdp_growth")
    if gdp_growth is not None and isinstance(gdp_growth, (int, float)):
        if float(gdp_growth) > 2.5:
            confidence += 0.1
        elif float(gdp_growth) < 0:
            confidence -= 0.1
    
    # Recession probability
    recession_prob = macro.get("recession_probability")
    if recession_prob is not None and isinstance(recession_prob, (int, float)):
        prob = float(recession_prob)
        if prob < 0.2:
            confidence += 0.1
        elif prob > 0.5:
            confidence -= 0.15
    
    # Clamp to 0.5-0.8 range
    return round(max(0.5, min(confidence, 0.8)), 2)


def calculate_final_confidence(
    technical: float,
    fundamental: float,
    sentiment: float,
    macro: float,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Calculate final multi-factor confidence using weighted average.
    
    Default weights:
    - Technical: 25% (lowest weight, most unreliable alone)
    - Fundamental: 35% (highest weight, most reliable)
    - Sentiment: 20% (narrative-driven, important for tech stocks)
    - Macro: 20% (regime-driven, important for portfolio construction)
    """
    if weights is None:
        weights = {
            "technical": 0.25,
            "fundamental": 0.35,
            "sentiment": 0.20,
            "macro": 0.20,
        }
    
    # Normalize weights
    total_weight = sum(weights.values())
    normalized_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Calculate weighted average
    final_confidence = (
        technical * normalized_weights["technical"] +
        fundamental * normalized_weights["fundamental"] +
        sentiment * normalized_weights["sentiment"] +
        macro * normalized_weights["macro"]
    )
    
    return {
        "final_confidence": round(final_confidence, 2),
        "components": {
            "technical": technical,
            "fundamental": fundamental,
            "sentiment": sentiment,
            "macro": macro,
        },
        "weights": normalized_weights,
    }


def compute_multi_factor_confidence(
    tech: dict[str, Any],
    fundamentals: dict[str, Any],
    sentiment: dict[str, Any],
    macro: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Main entry point: compute multi-factor confidence for a stock.
    
    Returns:
    {
        "final_confidence": 0.0-1.0,
        "components": {
            "technical": 0.0-0.6,
            "fundamental": 0.5-0.8,
            "sentiment": 0.4-0.8,
            "macro": 0.5-0.8,
        },
        "weights": {...},
        "confidence_label": "low" | "moderate" | "high",
    }
    """
    try:
        tech_conf = calculate_technical_confidence(tech)
        fund_conf = calculate_fundamental_confidence(fundamentals)
        sent_conf = calculate_sentiment_confidence(sentiment)
        macro_conf = calculate_macro_confidence(macro or {})
        
        result = calculate_final_confidence(tech_conf, fund_conf, sent_conf, macro_conf)
        
        # Add confidence label
        final = result["final_confidence"]
        if final >= 0.7:
            label = "high"
        elif final >= 0.55:
            label = "moderate"
        else:
            label = "low"
        
        result["confidence_label"] = label
        
        logger.debug(
            "Multi-factor confidence: {:.2f} ({}) | "
            "Tech: {:.2f}, Fund: {:.2f}, Sent: {:.2f}, Macro: {:.2f}",
            final, label, tech_conf, fund_conf, sent_conf, macro_conf
        )
        
        return result
    except Exception as e:
        logger.error("Error computing multi-factor confidence: {}", e)
        return {
            "final_confidence": 0.5,
            "components": {
                "technical": 0.3,
                "fundamental": 0.5,
                "sentiment": 0.4,
                "macro": 0.5,
            },
            "weights": {
                "technical": 0.25,
                "fundamental": 0.35,
                "sentiment": 0.20,
                "macro": 0.20,
            },
            "confidence_label": "low",
            "error": str(e),
        }
