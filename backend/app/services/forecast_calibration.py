"""
Forecast Calibration - Ensures quantitative forecasts are presented with appropriate uncertainty.

CRITICAL: Your narratives now sound professional and institutional.
This means users may assume your quantitative forecasts are rigorous.
They are NOT. They are heuristic estimates.

This module ensures we communicate uncertainty appropriately.
"""

from __future__ import annotations

from typing import Any


class ForecastCalibration:
    """Calibrates forecast presentation to reflect actual confidence"""
    
    @staticmethod
    def format_expected_return(
        expected_return_pct: float,
        confidence: float,
    ) -> dict[str, str]:
        """
        Format expected return with appropriate uncertainty language.
        
        NOT: "Expected Return: 15.72%"
        BUT: "Growth-oriented portfolio profile" or "Moderate-to-high upside potential"
        
        Returns:
        {
            "display": str (what to show user),
            "caveat": str (uncertainty disclaimer),
            "category": str (low/moderate/high upside),
        }
        """
        # Determine category
        if expected_return_pct < -5:
            category = "negative_outlook"
        elif expected_return_pct < 0:
            category = "cautious_outlook"
        elif expected_return_pct < 5:
            category = "modest_upside"
        elif expected_return_pct < 12:
            category = "moderate_upside"
        elif expected_return_pct < 20:
            category = "elevated_upside"
        else:
            category = "aggressive_upside"
        
        # Determine confidence qualifier
        if confidence < 0.45:
            confidence_text = "low conviction"
            confidence_category = "low"
        elif confidence < 0.55:
            confidence_text = "moderate conviction"
            confidence_category = "moderate"
        elif confidence < 0.70:
            confidence_text = "reasonable conviction"
            confidence_category = "moderate_high"
        else:
            confidence_text = "high conviction"
            confidence_category = "high"
        
        # Build display text
        if category == "negative_outlook":
            display = f"Cautious outlook ({confidence_text})"
        elif category == "cautious_outlook":
            display = f"Defensive positioning ({confidence_text})"
        elif category == "modest_upside":
            display = f"Modest upside potential ({confidence_text})"
        elif category == "moderate_upside":
            display = f"Moderate upside potential ({confidence_text})"
        elif category == "elevated_upside":
            display = f"Elevated upside potential ({confidence_text})"
        else:
            display = f"Aggressive upside potential ({confidence_text})"
        
        # Build caveat
        caveat = (
            "This is a heuristic estimate based on technical, fundamental, and sentiment analysis. "
            "It is NOT a financial forecast and should not be relied upon for investment decisions. "
            "Actual returns may differ materially. Past performance does not guarantee future results."
        )
        
        return {
            "display": display,
            "caveat": caveat,
            "category": category,
            "confidence_category": confidence_category,
            "numeric_estimate": f"{expected_return_pct:.1f}%",  # For reference only
        }
    
    @staticmethod
    def format_portfolio_return(
        total_expected_return: float,
        allocations: list[dict[str, Any]],
    ) -> dict[str, str]:
        """
        Format portfolio-level expected return.
        
        Returns:
        {
            "display": str,
            "caveat": str,
            "range": str (e.g., "5-15% range"),
        }
        """
        # Calculate confidence-weighted average
        total_confidence = 0.0
        total_weight = 0.0
        
        for alloc in allocations:
            weight = alloc.get("allocation_pct", 0) / 100.0
            confidence = alloc.get("confidence", {}).get("final_confidence", 0.5)
            total_confidence += weight * confidence
            total_weight += weight
        
        avg_confidence = total_confidence / total_weight if total_weight > 0 else 0.5
        
        # Determine range based on confidence
        if avg_confidence < 0.45:
            range_text = "Wide range of outcomes possible"
            display = "Uncertain outlook - wide range of potential outcomes"
        elif avg_confidence < 0.55:
            range_text = f"{total_expected_return - 8:.0f}% to {total_expected_return + 8:.0f}% range"
            display = f"Moderate conviction portfolio - {range_text}"
        elif avg_confidence < 0.70:
            range_text = f"{total_expected_return - 5:.0f}% to {total_expected_return + 5:.0f}% range"
            display = f"Reasonable conviction portfolio - {range_text}"
        else:
            range_text = f"{total_expected_return - 3:.0f}% to {total_expected_return + 3:.0f}% range"
            display = f"Higher conviction portfolio - {range_text}"
        
        caveat = (
            "Portfolio return estimates are heuristic and subject to significant uncertainty. "
            "Actual returns depend on market conditions, execution, and unforeseen events. "
            "This is decision-support analysis, not investment advice."
        )
        
        return {
            "display": display,
            "caveat": caveat,
            "range": range_text,
            "numeric_estimate": f"{total_expected_return:.1f}%",  # For reference only
            "confidence": avg_confidence,
        }
    
    @staticmethod
    def format_risk_score(
        risk_score: float,
        risk_tolerance: str,
    ) -> dict[str, str]:
        """
        Format risk score with appropriate context.
        
        Returns:
        {
            "display": str,
            "caveat": str,
            "alignment": str (aligned/misaligned/neutral),
        }
        """
        if risk_score < 30:
            risk_category = "low"
        elif risk_score < 50:
            risk_category = "moderate"
        elif risk_score < 70:
            risk_category = "elevated"
        else:
            risk_category = "high"
        
        # Check alignment with tolerance
        tolerance_map = {
            "low": ["low", "moderate"],
            "medium": ["low", "moderate", "elevated"],
            "high": ["moderate", "elevated", "high"],
        }
        
        aligned = risk_category in tolerance_map.get(risk_tolerance, [])
        
        if aligned:
            alignment = "aligned"
            alignment_text = "Portfolio risk profile aligns with stated tolerance"
        else:
            alignment = "misaligned"
            alignment_text = f"Portfolio risk ({risk_category}) exceeds stated tolerance ({risk_tolerance})"
        
        display = f"{risk_category.capitalize()} risk profile ({risk_score:.0f}/100) - {alignment_text}"
        
        caveat = (
            "Risk scores are estimates based on volatility, beta, and portfolio composition. "
            "Actual risk may differ due to market conditions and correlation changes."
        )
        
        return {
            "display": display,
            "caveat": caveat,
            "alignment": alignment,
            "risk_category": risk_category,
            "numeric_score": f"{risk_score:.0f}",
        }
    
    @staticmethod
    def build_forecast_disclaimer() -> str:
        """Build comprehensive forecast disclaimer"""
        return (
            "## Important Disclaimer\n\n"
            "This analysis is **decision-support research**, not investment advice.\n\n"
            "**Forecast Limitations:**\n"
            "- Expected returns are heuristic estimates, not rigorous forecasts\n"
            "- Risk scores are based on historical volatility and may not predict future risk\n"
            "- Confidence levels reflect data quality, not forecast accuracy\n"
            "- Actual results may differ materially from estimates\n\n"
            "**Key Risks:**\n"
            "- Market regime changes can invalidate technical analysis\n"
            "- Earnings surprises can cause rapid repricing\n"
            "- Macro shocks (rates, inflation, geopolitics) can dominate returns\n"
            "- Sector rotation can significantly impact concentrated portfolios\n\n"
            "**Recommendations:**\n"
            "- Use this analysis as one input among many\n"
            "- Maintain diversification and risk management discipline\n"
            "- Monitor portfolio regularly and rebalance as needed\n"
            "- Consult with a financial advisor for personalized guidance\n"
        )
