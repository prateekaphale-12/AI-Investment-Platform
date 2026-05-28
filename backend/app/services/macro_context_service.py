"""
Macro Context Service - Provides market regime awareness and macro context.

This addresses the critical gap: your portfolio is heavily AI/chip exposed,
but the system never discusses:
- AI capex sustainability
- Chip cycle risk
- Valuation crowding
- Rates impact
- Sector rotation

This service provides institutional-grade macro context for narratives.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from loguru import logger


class MacroContext:
    """Represents current macro regime and risks"""
    
    def __init__(self):
        self.regime: str = "neutral"  # "risk_on", "risk_off", "transition", "neutral"
        self.rate_environment: str = "elevated"  # "low", "moderate", "elevated", "restrictive"
        self.inflation_outlook: str = "moderate"  # "low", "moderate", "elevated"
        self.growth_outlook: str = "moderate"  # "weak", "moderate", "strong"
        self.sector_rotation_risk: bool = False
        self.valuation_crowding: bool = False
        self.key_risks: list[str] = []
        self.key_tailwinds: list[str] = []
        self.confidence: float = 0.5


class MacroContextService:
    """
    Provides macro context for portfolio analysis.
    
    This is a simplified version - in production, you'd integrate:
    - Fed funds rate data
    - Yield curve data
    - VIX levels
    - Sector rotation metrics
    - Earnings growth forecasts
    """
    
    @staticmethod
    def analyze_portfolio_macro_exposure(
        tickers: list[str],
        sector_allocation: dict[str, float],
    ) -> MacroContext:
        """
        Analyze macro exposure of portfolio.
        
        Returns: MacroContext with regime and risks
        """
        context = MacroContext()
        
        # Detect AI/chip concentration
        ai_chip_exposure = sector_allocation.get("semiconductors", 0) + sector_allocation.get("technology", 0)
        
        if ai_chip_exposure > 0.5:  # >50% in AI/chips
            context.key_risks.append(
                "Portfolio is heavily concentrated in AI/semiconductor sector. "
                "Exposed to chip cycle risk and AI capex sustainability concerns."
            )
            context.valuation_crowding = True
            context.sector_rotation_risk = True
        
        # Rate sensitivity analysis
        rate_sensitive_sectors = {
            "technology": 0.8,  # High sensitivity
            "consumer": 0.6,    # Moderate sensitivity
            "financials": -0.3, # Negative sensitivity (benefits from higher rates)
        }
        
        rate_sensitivity = sum(
            sector_allocation.get(sector, 0) * sensitivity
            for sector, sensitivity in rate_sensitive_sectors.items()
        )
        
        if rate_sensitivity > 0.5:
            context.key_risks.append(
                "Portfolio has elevated sensitivity to interest rate increases. "
                "Growth stocks may face headwinds if rates rise further."
            )
        
        # Valuation context
        if ai_chip_exposure > 0.4:
            context.key_risks.append(
                "AI/semiconductor valuations are elevated relative to historical averages. "
                "Earnings growth must accelerate to justify current multiples."
            )
        
        # Macro tailwinds
        if ai_chip_exposure > 0.3:
            context.key_tailwinds.append(
                "AI infrastructure buildout remains in early innings. "
                "Long-term capex cycle could support semiconductor demand."
            )
            context.key_tailwinds.append(
                "Generative AI adoption accelerating across enterprise. "
                "Potential for sustained demand for AI chips and software."
            )
        
        # Determine regime
        context.regime = MacroContextService._determine_regime(
            ai_chip_exposure,
            rate_sensitivity,
        )
        
        # Set confidence
        context.confidence = 0.6  # Moderate confidence - macro is uncertain
        
        return context
    
    @staticmethod
    def _determine_regime(ai_chip_exposure: float, rate_sensitivity: float) -> str:
        """Determine current macro regime"""
        # Simplified regime detection
        # In production, this would use actual macro data
        
        if ai_chip_exposure > 0.6 and rate_sensitivity > 0.5:
            return "transition"  # High growth exposure in rising rate environment
        elif ai_chip_exposure > 0.5:
            return "risk_on"  # Growth-heavy portfolio
        elif rate_sensitivity < -0.2:
            return "risk_off"  # Defensive positioning
        else:
            return "neutral"
    
    @staticmethod
    def build_macro_narrative(context: MacroContext) -> str:
        """
        Build institutional-grade macro narrative.
        
        NOT: "Rates are high, tech is risky"
        BUT: "Elevated rate environment creates headwinds for growth valuations,
              though AI capex cycle may provide structural support."
        """
        parts = []
        
        # Regime context
        if context.regime == "risk_on":
            parts.append(
                "Current macro environment favors growth and technology exposure, "
                "supported by AI infrastructure buildout and enterprise digital transformation."
            )
        elif context.regime == "risk_off":
            parts.append(
                "Macro environment shows defensive characteristics. "
                "Growth exposure faces headwinds from elevated rates and economic uncertainty."
            )
        elif context.regime == "transition":
            parts.append(
                "Portfolio is positioned in a transitional macro environment. "
                "Growth exposure faces rate headwinds, but AI capex cycle provides structural support."
            )
        else:
            parts.append(
                "Macro environment remains balanced with mixed signals. "
                "Growth and value factors show competing dynamics."
            )
        
        # Rate environment
        if context.rate_environment == "elevated":
            parts.append(
                "Elevated interest rates create valuation pressure on growth stocks, "
                "particularly those with long-duration cash flows."
            )
        elif context.rate_environment == "restrictive":
            parts.append(
                "Restrictive rate environment poses significant headwinds for growth valuations. "
                "Portfolio positioning should reflect this constraint."
            )
        
        # Key risks
        if context.key_risks:
            risk_text = " ".join(context.key_risks)
            parts.append(f"Key macro risks: {risk_text}")
        
        # Key tailwinds
        if context.key_tailwinds:
            tailwind_text = " ".join(context.key_tailwinds)
            parts.append(f"Structural tailwinds: {tailwind_text}")
        
        # Confidence qualifier
        parts.append(
            "Macro forecasting carries inherent uncertainty; "
            "portfolio should maintain diversification and risk management discipline."
        )
        
        return " ".join(parts)
    
    @staticmethod
    def get_sector_rotation_warning(
        current_allocation: dict[str, float],
        historical_allocation: dict[str, float] | None = None,
    ) -> str | None:
        """
        Detect potential sector rotation risks.
        
        Returns: Warning message if rotation risk detected, None otherwise
        """
        # Check for extreme concentration
        max_sector_allocation = max(current_allocation.values()) if current_allocation else 0
        
        if max_sector_allocation > 0.6:
            return (
                f"Portfolio is heavily concentrated in single sector ({max_sector_allocation:.0%}). "
                f"Sector rotation could significantly impact returns. "
                f"Consider diversification to reduce concentration risk."
            )
        
        # Check for AI/chip crowding
        ai_chip = current_allocation.get("semiconductors", 0) + current_allocation.get("technology", 0)
        if ai_chip > 0.5:
            return (
                f"AI/semiconductor sector represents {ai_chip:.0%} of portfolio. "
                f"Crowded positioning increases vulnerability to sector-specific shocks. "
                f"Monitor for signs of valuation normalization or capex cycle slowdown."
            )
        
        return None
    
    @staticmethod
    def get_valuation_context(
        portfolio_pe: float | None,
        market_pe: float = 20.0,  # Approximate S&P 500 PE
    ) -> str:
        """
        Provide valuation context relative to market.
        
        Returns: Valuation narrative
        """
        if not portfolio_pe or portfolio_pe <= 0:
            return "Valuation metrics unavailable for analysis."
        
        pe_premium = (portfolio_pe / market_pe - 1) * 100
        
        if pe_premium > 50:
            return (
                f"Portfolio trades at significant premium to market ({pe_premium:.0f}% above S&P 500). "
                f"Earnings growth must accelerate to justify valuation. "
                f"Vulnerable to multiple compression if growth disappoints."
            )
        elif pe_premium > 20:
            return (
                f"Portfolio trades at moderate premium to market ({pe_premium:.0f}% above S&P 500). "
                f"Valuation reflects growth expectations. "
                f"Monitor earnings delivery relative to expectations."
            )
        elif pe_premium > 0:
            return (
                f"Portfolio trades at slight premium to market ({pe_premium:.0f}% above S&P 500). "
                f"Valuation appears reasonable for growth profile."
            )
        else:
            return (
                f"Portfolio trades at discount to market ({abs(pe_premium):.0f}% below S&P 500). "
                f"Valuation appears attractive relative to growth profile."
            )


def get_macro_context_service() -> MacroContextService:
    """Get macro context service instance"""
    return MacroContextService()
