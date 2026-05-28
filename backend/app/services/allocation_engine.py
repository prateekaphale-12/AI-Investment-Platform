"""
Confidence-driven portfolio allocation engine.

Replaces equal-weight allocation with intelligent weighting based on:
- Confidence scores (technical, fundamental, sentiment, macro)
- Volatility (beta)
- Risk tolerance
- Sector constraints
- Correlation

Example:
- GOOGL bullish, high confidence (0.75), low beta → 22% allocation
- CRM bearish, moderate confidence (0.55), high beta → 6% allocation
- MSFT mixed, low confidence (0.45), medium beta → 4% allocation
"""

from __future__ import annotations

from typing import Any, Literal
from loguru import logger

Risk = Literal["low", "medium", "high"]


def _risk_score_from(beta: float | None, signal: str, confidence: float = 0.5, ytd_return: float = 0.0) -> float:
    """
    Calculate RISK score (0-100) based on VOLATILITY, not momentum.
    
    CRITICAL: Risk ≠ Opportunity
    - High-growth stocks (NVDA, MU) = HIGH RISK (high volatility)
    - Stable stocks (MSFT, AAPL) = MODERATE RISK (lower volatility)
    - Signal (bullish/bearish) does NOT reduce risk
    
    Risk factors:
    1. Beta (systematic volatility) - PRIMARY FACTOR
    2. YTD return magnitude (high returns = high volatility) - SECONDARY
    3. Confidence (low confidence = higher uncertainty risk)
    
    Signal does NOT affect risk score (bullish doesn't mean less risky).
    """
    base = 40.0
    
    # PRIMARY: Beta component (systematic risk/volatility)
    # This is the main driver of risk
    if beta is not None and isinstance(beta, (int, float)):
        beta_float = float(beta)
        # Beta 0.8 = 40, Beta 1.0 = 50, Beta 1.5 = 67.5, Beta 2.0 = 85
        base = min(95.0, max(15.0, 30.0 + beta_float * 35.0))
    
    # SECONDARY: YTD return magnitude (high returns often = high volatility)
    # Stocks with extreme returns are riskier
    abs_return = abs(ytd_return)
    if abs_return > 100:
        base += 20  # Extreme returns = high risk
    elif abs_return > 50:
        base += 12  # Very high returns = elevated risk
    elif abs_return > 30:
        base += 6   # High returns = some additional risk
    
    # Confidence component (low confidence = higher uncertainty risk)
    # This is a MODIFIER, not primary
    if confidence < 0.45:
        base += 8   # Low confidence = higher risk
    elif confidence > 0.75:
        base -= 3   # High confidence = slightly lower risk
    
    # IMPORTANT: Signal does NOT affect risk
    # Bullish signal doesn't make a volatile stock less risky
    # Bearish signal doesn't make a stable stock more risky
    
    return round(max(10.0, min(100.0, base)), 1)


def _expected_return_heuristic(
    ytd_return_pct: float,
    signal: str,
    confidence: float = 0.5,
    beta: float | None = None,
) -> float:
    """
    Calculate expected return heuristic (NOT a rigorous forecast).
    
    CRITICAL NOTES:
    - This is a HEURISTIC ESTIMATE, not a financial forecast
    - Should be displayed with caveats about uncertainty
    - Range: -10% to +15% (conservative)
    - Accounts for mean reversion (high past returns don't predict future)
    
    Methodology:
    1. Base: 20% of YTD return (mean reversion adjustment)
    2. Signal adjustment: ±1-2%
    3. Confidence adjustment: ±1%
    4. Beta adjustment: High volatility = lower expected return (risk premium)
    
    This is MUCH more conservative than the old 35% of YTD return.
    """
    # BASE: Only 20% of YTD return (mean reversion)
    # High past returns don't predict high future returns
    raw = ytd_return_pct * 0.20
    
    # Signal adjustment (modest impact)
    if signal == "bullish":
        raw += 1.5
    elif signal == "bearish":
        raw -= 1.5
    elif signal == "bullish_but_extended":
        raw += 0.5  # Less bullish due to extension
    elif signal == "bearish_but_oversold":
        raw -= 0.5  # Less bearish due to oversold
    
    # Confidence adjustment (modest impact)
    if confidence >= 0.75:
        raw += 1.0
    elif confidence >= 0.60:
        raw += 0.5
    elif confidence < 0.45:
        raw -= 1.0
    
    # Beta adjustment (high volatility = lower expected return)
    # This accounts for risk premium
    if beta is not None and isinstance(beta, (int, float)):
        beta_float = float(beta)
        if beta_float > 1.5:
            raw -= 2.0  # High beta = lower expected return
        elif beta_float > 1.2:
            raw -= 1.0
        elif beta_float < 0.8:
            raw += 0.5  # Low beta = slight premium
    
    # Clamp to realistic range: -10% to +15%
    # This prevents unrealistic expectations
    return round(max(-10.0, min(15.0, raw)), 2)


def _calculate_confidence_weight(
    confidence: float,
    avg_confidence: float,
    risk_tolerance: Risk,
) -> float:
    """
    Calculate weight adjustment based on confidence.
    
    High confidence → MUCH higher weight
    Low confidence → MUCH lower weight
    Risk tolerance affects how much we deviate from average
    
    AGGRESSIVE WEIGHTING: 0.5x to 1.8x (not 0.9x to 1.1x)
    """
    if avg_confidence == 0:
        return 1.0
    
    # Confidence ratio
    ratio = confidence / avg_confidence
    
    # Risk tolerance affects confidence weighting (MORE AGGRESSIVE)
    if risk_tolerance == "high":
        # High risk: amplify confidence differences MUCH more
        weight = ratio ** 1.8  # Was 1.2, now 1.8
    elif risk_tolerance == "low":
        # Low risk: still differentiate, but less extreme
        weight = ratio ** 1.2  # Was 0.8, now 1.2
    else:
        # Medium risk: moderate amplification
        weight = ratio ** 1.5  # Was 1.0, now 1.5
    
    # Clamp to reasonable range (0.5x to 1.8x)
    return max(0.5, min(weight, 1.8))


def _calculate_volatility_adjustment(
    beta: float | None,
    risk_tolerance: Risk,
) -> float:
    """
    Adjust weight based on volatility (beta).
    
    Low risk tolerance: reduce high-beta stocks MORE
    High risk tolerance: increase high-beta stocks MORE
    
    AGGRESSIVE ADJUSTMENT: 0.7x to 1.3x (not 0.85x to 1.15x)
    """
    if beta is None or not isinstance(beta, (int, float)):
        return 1.0
    
    beta_float = float(beta)
    
    if risk_tolerance == "low":
        # Penalize high-beta stocks MORE aggressively
        if beta_float > 1.5:
            return 0.70  # Was 0.85, now 0.70
        elif beta_float > 1.2:
            return 0.85  # Was 0.85, now 0.85
        elif beta_float < 0.8:
            return 1.20  # Was 1.1, now 1.20
        elif beta_float < 1.0:
            return 1.10
    elif risk_tolerance == "high":
        # Reward high-beta stocks MORE aggressively
        if beta_float > 1.5:
            return 1.30  # Was 1.15, now 1.30
        elif beta_float > 1.2:
            return 1.15  # Was 1.15, now 1.15
        elif beta_float < 0.8:
            return 0.85  # Was 0.9, now 0.85
        elif beta_float < 1.0:
            return 0.95
    else:
        # Medium risk: moderate adjustment
        if beta_float > 1.5:
            return 0.90
        elif beta_float > 1.2:
            return 0.95
        elif beta_float < 0.8:
            return 1.10
        elif beta_float < 1.0:
            return 1.05
    
    return 1.0


def calculate_confidence_driven_weights(
    tickers_data: list[dict[str, Any]],
    risk_tolerance: Risk,
) -> list[float]:
    """
    Calculate portfolio weights based on confidence and risk factors.
    
    Returns normalized weights (sum to 100).
    
    AGGRESSIVE WEIGHTING:
    - Bullish + high confidence → 1.5-1.8x weight
    - Bearish + low confidence → 0.4-0.6x weight
    - Uses risk_score to further adjust
    """
    if not tickers_data:
        return []
    
    n = len(tickers_data)
    base_weight = 100.0 / n
    
    # Extract confidence scores
    confidences = []
    for row in tickers_data:
        conf_data = row.get("confidence", {})
        final_conf = conf_data.get("final_confidence", 0.5)
        confidences.append(final_conf)
    
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
    
    # Calculate raw weights
    weights = []
    for i, row in enumerate(tickers_data):
        # Start with base weight
        w = base_weight
        
        # Confidence adjustment (PRIMARY FACTOR - most aggressive)
        conf_data = row.get("confidence", {})
        confidence = conf_data.get("final_confidence", 0.5)
        conf_weight = _calculate_confidence_weight(confidence, avg_confidence, risk_tolerance)
        w *= conf_weight
        
        # Volatility adjustment (SECONDARY FACTOR)
        market = row.get("market", {})
        info = market.get("info", {}) if isinstance(market.get("info"), dict) else {}
        beta = info.get("beta")
        vol_weight = _calculate_volatility_adjustment(beta, risk_tolerance)
        w *= vol_weight
        
        # Signal adjustment (AGGRESSIVE - was 1.02/0.98, now much stronger)
        tech = row.get("technical", {})
        signal = tech.get("signal", "neutral")
        if signal == "bullish":
            w *= 1.25  # Was 1.02, now 1.25 (25% boost)
        elif signal == "bearish":
            w *= 0.60  # Was 0.98, now 0.60 (40% penalty)
        elif signal == "bullish_but_extended":
            w *= 1.10  # Bullish but risky
        elif signal == "bearish_but_oversold":
            w *= 0.80  # Bearish but potential bounce
        elif signal == "mixed":
            w *= 0.90  # Uncertainty penalty
        
        # Risk score adjustment (NEW - use the risk_score we calculate)
        # High risk score → lower weight
        risk_score = _risk_score_from(
            beta if isinstance(beta, (int, float)) else None,
            signal,
            confidence,
            ytd if isinstance(ytd, (int, float)) else 0.0
        )
        if risk_score > 75:
            w *= 0.85  # High risk = reduce weight
        elif risk_score > 65:
            w *= 0.92
        elif risk_score < 45:
            w *= 1.10  # Low risk = increase weight
        elif risk_score < 55:
            w *= 1.05
        
        weights.append(w)
    
    # Normalize to 100%
    total = sum(weights)
    if total > 0:
        weights = [w / total * 100.0 for w in weights]
    else:
        weights = [base_weight] * n
    
    return weights


def build_allocations_confidence_driven(
    budget: float,
    risk_tolerance: Risk,
    tickers_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Build portfolio allocations using confidence-driven weighting.
    
    tickers_data items should include:
    - ticker
    - market (with info.beta, ytd_return_pct)
    - technical (with signal, confidence)
    - confidence (with final_confidence, components)
    - sentiment
    - rationale
    """
    if not tickers_data:
        return [], {
            "total_budget": budget,
            "total_expected_return": 0.0,
            "overall_risk": risk_tolerance,
            "diversification_score": 0.0,
            "best_performer": None,
            "recommended_action": "Insufficient data for allocation.",
        }
    
    # Calculate confidence-driven weights
    weights = calculate_confidence_driven_weights(tickers_data, risk_tolerance)
    
    allocations: list[dict[str, Any]] = []
    exp_returns: list[float] = []
    
    for w, row in zip(weights, tickers_data, strict=True):
        ticker = row["ticker"]
        market = row.get("market", {})
        technical = row.get("technical", {})
        confidence_data = row.get("confidence", {})
        
        # Extract data
        info = market.get("info", {}) if isinstance(market.get("info"), dict) else {}
        beta = info.get("beta")
        ytd = float(market.get("ytd_return_pct", 0.0))
        signal = technical.get("signal", "neutral")
        final_confidence = confidence_data.get("final_confidence", 0.5)
        
        # Calculate metrics
        er = _expected_return_heuristic(
            ytd, 
            signal, 
            final_confidence,
            beta if isinstance(beta, (int, float)) else None
        )
        exp_returns.append(er * (w / 100.0))
        
        risk_score = _risk_score_from(
            beta if isinstance(beta, (int, float)) else None,
            signal,
            final_confidence,
            ytd
        )
        
        rationale = row.get("rationale", {})
        
        allocations.append({
            "ticker": ticker,
            "allocation_pct": round(w, 2),
            "amount": round(budget * w / 100.0, 2),
            "expected_return": er,
            "risk_score": risk_score,
            "confidence": round(final_confidence * 100, 1),
            "rationale": rationale,
        })
    
    # Calculate summary metrics
    total_er = round(sum(exp_returns), 2)
    best = max(
        tickers_data,
        key=lambda r: float((r.get("market", {}).get("ytd_return_pct") or 0.0))
    )
    
    # Diversification score: based on number of stocks and weight distribution
    n = len(tickers_data)
    div_score = min(100.0, 50.0 + n * 8.0)
    
    # Adjust for concentration (if one stock >30%, reduce score)
    max_weight = max(weights) if weights else 0
    if max_weight > 30:
        div_score *= (1 - (max_weight - 30) / 70 * 0.3)
    
    summary = {
        "total_budget": budget,
        "total_expected_return": total_er,
        "overall_risk": risk_tolerance,
        "diversification_score": round(div_score, 1),
        "best_performer": best.get("ticker"),
        "recommended_action": "Research & due diligence only — not investment advice.",
    }
    
    logger.info(
        "Confidence-driven allocation: {} stocks, avg confidence {:.1f}%, "
        "total expected return {:.2f}%, diversification {:.1f}",
        n,
        sum(c.get("confidence", {}).get("final_confidence", 0.5) for c in tickers_data) / n * 100,
        total_er,
        div_score
    )
    
    return allocations, summary
