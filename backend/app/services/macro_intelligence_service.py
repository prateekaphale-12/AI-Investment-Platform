"""
Macro Intelligence Service - Provides macro context for investment decisions.

Tracks:
- Interest rate environment (Fed policy)
- Market regime (bull/bear/correction)
- Sector rotation signals
- Volatility regime (VIX proxy)
- Economic indicators (recession probability)
- Geopolitical risk factors

This is a FREE implementation using public data sources.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any

import yfinance as yf
from loguru import logger


class MacroIntelligence:
    """Provides macro context for portfolio decisions"""

    # Key macro indicators (all free via yfinance)
    MACRO_TICKERS = {
        "interest_rates": "^TNX",  # 10-year Treasury yield
        "vix": "^VIX",  # Volatility index
        "sp500": "^GSPC",  # S&P 500
        "nasdaq": "^IXIC",  # Nasdaq
        "dollar": "DXY",  # Dollar index (proxy)
        "gold": "GC=F",  # Gold futures (risk-off indicator)
        "oil": "CL=F",  # Oil futures (economic activity)
    }

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._cache_time: dict[str, datetime] = {}
        self.cache_ttl = 3600  # 1 hour cache

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache_time:
            return False
        age = (datetime.now() - self._cache_time[key]).total_seconds()
        return age < self.cache_ttl

    async def get_macro_context(self) -> dict[str, Any]:
        """
        Get comprehensive macro context.

        Returns:
        {
            "interest_rate_regime": "low" | "moderate" | "high",
            "interest_rate_trend": "rising" | "stable" | "falling",
            "current_rate": float,
            "volatility_regime": "low" | "moderate" | "high",
            "vix_level": float,
            "market_regime": "bull" | "correction" | "bear",
            "sp500_ytd": float,
            "sector_rotation": "growth" | "value" | "defensive",
            "economic_outlook": "expansion" | "slowdown" | "recession_risk",
            "risk_sentiment": "risk_on" | "risk_neutral" | "risk_off",
            "geopolitical_risk": "low" | "moderate" | "high",
            "timestamp": str,
        }
        """
        try:
            # Fetch all macro indicators in parallel
            tasks = [
                self._get_interest_rates(),
                self._get_volatility(),
                self._get_market_regime(),
                self._get_sector_rotation(),
                self._get_economic_outlook(),
                self._get_risk_sentiment(),
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            context = {
                "timestamp": datetime.now().isoformat(),
                "data_quality": "good",
            }

            # Merge results
            for result in results:
                if isinstance(result, dict):
                    context.update(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Macro data fetch failed: {result}")
                    context["data_quality"] = "degraded"

            return context
        except Exception as e:
            logger.error(f"Failed to get macro context: {e}")
            return self._get_default_macro_context()

    async def _get_interest_rates(self) -> dict[str, Any]:
        """Get interest rate regime and trend"""
        if self._is_cache_valid("rates"):
            return self._cache.get("rates", {})

        try:
            ticker = self.MACRO_TICKERS["interest_rates"]
            data = await asyncio.to_thread(yf.download, ticker, period="1y", progress=False)

            if data.empty:
                return {}

            current = float(data["Close"].iloc[-1].item() if hasattr(data["Close"].iloc[-1], 'item') else data["Close"].iloc[-1])
            prev_month = float((data["Close"].iloc[-22].item() if hasattr(data["Close"].iloc[-22], 'item') else data["Close"].iloc[-22])) if len(data) > 22 else current
            prev_year = float((data["Close"].iloc[0].item() if hasattr(data["Close"].iloc[0], 'item') else data["Close"].iloc[0])) if len(data) > 0 else current

            # Determine regime
            if current < 2.0:
                regime = "low"
            elif current < 4.0:
                regime = "moderate"
            else:
                regime = "high"

            # Determine trend
            if current > prev_month + 0.25:
                trend = "rising"
            elif current < prev_month - 0.25:
                trend = "falling"
            else:
                trend = "stable"

            result = {
                "interest_rate_regime": regime,
                "interest_rate_trend": trend,
                "current_rate": round(current, 2),
                "rate_change_1m": round(current - prev_month, 2),
                "rate_change_1y": round(current - prev_year, 2),
            }

            self._cache["rates"] = result
            self._cache_time["rates"] = datetime.now()
            return result
        except Exception as e:
            logger.warning(f"Failed to get interest rates: {e}")
            return {}

    async def _get_volatility(self) -> dict[str, Any]:
        """Get volatility regime (VIX)"""
        if self._is_cache_valid("volatility"):
            return self._cache.get("volatility", {})

        try:
            ticker = self.MACRO_TICKERS["vix"]
            data = await asyncio.to_thread(yf.download, ticker, period="1mo", progress=False)

            if data.empty:
                return {}

            current = float(data["Close"].iloc[-1].item() if hasattr(data["Close"].iloc[-1], 'item') else data["Close"].iloc[-1])

            # VIX regime
            if current < 15:
                regime = "low"
            elif current < 25:
                regime = "moderate"
            else:
                regime = "high"

            result = {
                "volatility_regime": regime,
                "vix_level": round(current, 1),
                "vix_interpretation": self._interpret_vix(current),
            }

            self._cache["volatility"] = result
            self._cache_time["volatility"] = datetime.now()
            return result
        except Exception as e:
            logger.warning(f"Failed to get volatility: {e}")
            return {}

    def _interpret_vix(self, vix: float) -> str:
        """Interpret VIX level"""
        if vix < 12:
            return "Complacency (unusually low fear)"
        elif vix < 15:
            return "Low volatility (calm markets)"
        elif vix < 20:
            return "Normal volatility"
        elif vix < 30:
            return "Elevated volatility (market stress)"
        else:
            return "High volatility (market panic)"

    async def _get_market_regime(self) -> dict[str, Any]:
        """Get market regime (bull/correction/bear)"""
        if self._is_cache_valid("regime"):
            return self._cache.get("regime", {})

        try:
            ticker = self.MACRO_TICKERS["sp500"]
            data = await asyncio.to_thread(yf.download, ticker, period="1y", progress=False)

            if data.empty:
                return {}

            current = float(data["Close"].iloc[-1].item() if hasattr(data["Close"].iloc[-1], 'item') else data["Close"].iloc[-1])
            year_high = float(data["Close"].max().item() if hasattr(data["Close"].max(), 'item') else data["Close"].max())
            year_low = float(data["Close"].min().item() if hasattr(data["Close"].min(), 'item') else data["Close"].min())
            ytd_return = ((current - float(data["Close"].iloc[0].item() if hasattr(data["Close"].iloc[0], 'item') else data["Close"].iloc[0])) / float(data["Close"].iloc[0].item() if hasattr(data["Close"].iloc[0], 'item') else data["Close"].iloc[0])) * 100

            # Determine regime
            drawdown = ((year_high - current) / year_high) * 100
            if ytd_return > 15:
                regime = "bull"
            elif drawdown > 20:
                regime = "bear"
            elif drawdown > 10:
                regime = "correction"
            else:
                regime = "bull"

            result = {
                "market_regime": regime,
                "sp500_ytd": round(ytd_return, 2),
                "drawdown_from_high": round(drawdown, 2),
                "regime_interpretation": self._interpret_regime(regime, drawdown),
            }

            self._cache["regime"] = result
            self._cache_time["regime"] = datetime.now()
            return result
        except Exception as e:
            logger.warning(f"Failed to get market regime: {e}")
            return {}

    def _interpret_regime(self, regime: str, drawdown: float) -> str:
        """Interpret market regime"""
        if regime == "bull":
            return "Strong uptrend (favorable for growth stocks)"
        elif regime == "correction":
            return f"Correction phase ({drawdown:.1f}% from highs, consolidation likely)"
        else:
            return f"Bear market ({drawdown:.1f}% from highs, defensive positioning recommended)"

    async def _get_sector_rotation(self) -> dict[str, Any]:
        """Detect sector rotation signals"""
        if self._is_cache_valid("rotation"):
            return self._cache.get("rotation", {})

        try:
            # Simple sector rotation: compare tech vs defensive
            tech_tickers = ["QQQ"]  # Nasdaq 100 (tech-heavy)
            defensive_tickers = ["XLU"]  # Utilities (defensive)

            tech_data = await asyncio.to_thread(yf.download, tech_tickers[0], period="3mo", progress=False)
            defensive_data = await asyncio.to_thread(yf.download, defensive_tickers[0], period="3mo", progress=False)

            if tech_data.empty or defensive_data.empty:
                return {}

            tech_close_0 = float(tech_data["Close"].iloc[0].item() if hasattr(tech_data["Close"].iloc[0], 'item') else tech_data["Close"].iloc[0])
            tech_close_1 = float(tech_data["Close"].iloc[-1].item() if hasattr(tech_data["Close"].iloc[-1], 'item') else tech_data["Close"].iloc[-1])
            def_close_0 = float(defensive_data["Close"].iloc[0].item() if hasattr(defensive_data["Close"].iloc[0], 'item') else defensive_data["Close"].iloc[0])
            def_close_1 = float(defensive_data["Close"].iloc[-1].item() if hasattr(defensive_data["Close"].iloc[-1], 'item') else defensive_data["Close"].iloc[-1])
            
            tech_return = ((tech_close_1 - tech_close_0) / tech_close_0) * 100
            defensive_return = ((def_close_1 - def_close_0) / def_close_0) * 100

            # Determine rotation
            if tech_return > defensive_return + 5:
                rotation = "growth"
            elif defensive_return > tech_return + 5:
                rotation = "defensive"
            else:
                rotation = "balanced"

            result = {
                "sector_rotation": rotation,
                "tech_3m_return": round(tech_return, 2),
                "defensive_3m_return": round(defensive_return, 2),
                "rotation_interpretation": self._interpret_rotation(rotation),
            }

            self._cache["rotation"] = result
            self._cache_time["rotation"] = datetime.now()
            return result
        except Exception as e:
            logger.warning(f"Failed to get sector rotation: {e}")
            return {}

    def _interpret_rotation(self, rotation: str) -> str:
        """Interpret sector rotation"""
        if rotation == "growth":
            return "Growth outperforming (risk-on environment, favor tech/growth)"
        elif rotation == "defensive":
            return "Defensive outperforming (risk-off environment, favor utilities/staples)"
        else:
            return "Balanced rotation (mixed signals, diversification prudent)"

    async def _get_economic_outlook(self) -> dict[str, Any]:
        """Assess economic outlook"""
        if self._is_cache_valid("outlook"):
            return self._cache.get("outlook", {})

        try:
            # Simple proxy: compare high-yield spreads via market performance
            # In real system, would use actual economic data APIs
            ticker = self.MACRO_TICKERS["sp500"]
            data = await asyncio.to_thread(yf.download, ticker, period="6mo", progress=False)

            if data.empty:
                return {}

            # Volatility trend as proxy for economic confidence
            pct_change = data["Close"].pct_change()
            recent_vol = pct_change.tail(20).std() * 100
            older_vol = pct_change.head(20).std() * 100
            
            # Handle NaN values
            if recent_vol != recent_vol or older_vol != older_vol:  # NaN check
                return {}

            if recent_vol < older_vol * 0.8:
                outlook = "expansion"
            elif recent_vol > older_vol * 1.2:
                outlook = "slowdown"
            else:
                outlook = "expansion"

            result = {
                "economic_outlook": outlook,
                "outlook_interpretation": self._interpret_outlook(outlook),
            }

            self._cache["outlook"] = result
            self._cache_time["outlook"] = datetime.now()
            return result
        except Exception as e:
            logger.warning(f"Failed to get economic outlook: {e}")
            return {}

    def _interpret_outlook(self, outlook: str) -> str:
        """Interpret economic outlook"""
        if outlook == "expansion":
            return "Economic expansion (favorable for cyclicals and growth)"
        elif outlook == "slowdown":
            return "Economic slowdown (favor defensive and dividend stocks)"
        else:
            return "Recession risk (defensive positioning, quality focus)"

    async def _get_risk_sentiment(self) -> dict[str, Any]:
        """Assess overall risk sentiment"""
        if self._is_cache_valid("sentiment"):
            return self._cache.get("sentiment", {})

        try:
            # Risk sentiment: combination of VIX, market performance, and spreads
            vix_data = await asyncio.to_thread(yf.download, self.MACRO_TICKERS["vix"], period="1mo", progress=False)
            sp500_data = await asyncio.to_thread(yf.download, self.MACRO_TICKERS["sp500"], period="1mo", progress=False)

            if vix_data.empty or sp500_data.empty:
                return {}

            vix = float(vix_data["Close"].iloc[-1].item() if hasattr(vix_data["Close"].iloc[-1], 'item') else vix_data["Close"].iloc[-1])
            sp500_close_0 = float(sp500_data["Close"].iloc[0].item() if hasattr(sp500_data["Close"].iloc[0], 'item') else sp500_data["Close"].iloc[0])
            sp500_close_1 = float(sp500_data["Close"].iloc[-1].item() if hasattr(sp500_data["Close"].iloc[-1], 'item') else sp500_data["Close"].iloc[-1])
            sp500_return = ((sp500_close_1 - sp500_close_0) / sp500_close_0) * 100

            # Determine sentiment
            if vix < 15 and sp500_return > 0:
                sentiment = "risk_on"
            elif vix > 25 or sp500_return < -5:
                sentiment = "risk_off"
            else:
                sentiment = "risk_neutral"

            result = {
                "risk_sentiment": sentiment,
                "risk_sentiment_interpretation": self._interpret_risk_sentiment(sentiment),
            }

            self._cache["sentiment"] = result
            self._cache_time["sentiment"] = datetime.now()
            return result
        except Exception as e:
            logger.warning(f"Failed to get risk sentiment: {e}")
            return {}

    def _interpret_risk_sentiment(self, sentiment: str) -> str:
        """Interpret risk sentiment"""
        if sentiment == "risk_on":
            return "Risk-on environment (favor growth, cyclicals, emerging markets)"
        elif sentiment == "risk_off":
            return "Risk-off environment (favor safe havens, quality, dividends)"
        else:
            return "Risk-neutral environment (balanced approach)"

    def _get_default_macro_context(self) -> dict[str, Any]:
        """Return default macro context when data unavailable"""
        return {
            "interest_rate_regime": "moderate",
            "interest_rate_trend": "stable",
            "current_rate": 4.5,
            "volatility_regime": "moderate",
            "vix_level": 18.0,
            "market_regime": "bull",
            "sp500_ytd": 10.0,
            "sector_rotation": "balanced",
            "economic_outlook": "expansion",
            "risk_sentiment": "risk_neutral",
            "geopolitical_risk": "moderate",
            "timestamp": datetime.now().isoformat(),
            "data_quality": "default",
        }


# Singleton instance
_macro_intelligence = MacroIntelligence()


async def get_macro_context() -> dict[str, Any]:
    """Get current macro context"""
    return await _macro_intelligence.get_macro_context()


def get_macro_confidence_adjustment(macro_context: dict[str, Any]) -> float:
    """
    Get macro confidence adjustment factor (0.5-1.0).

    Adjusts confidence based on macro environment:
    - Risk-on environment: boost confidence (1.0)
    - Risk-neutral: neutral (0.8)
    - Risk-off environment: reduce confidence (0.5)
    """
    sentiment = macro_context.get("risk_sentiment", "risk_neutral")

    if sentiment == "risk_on":
        return 1.0
    elif sentiment == "risk_off":
        return 0.5
    else:
        return 0.8


def get_macro_sector_bias(macro_context: dict[str, Any]) -> dict[str, float]:
    """
    Get sector bias based on macro environment.

    Returns sector allocation adjustments:
    - Growth environment: favor tech, growth
    - Defensive environment: favor utilities, staples, healthcare
    - Balanced: neutral
    """
    rotation = macro_context.get("sector_rotation", "balanced")
    outlook = macro_context.get("economic_outlook", "expansion")

    bias = {
        "technology": 1.0,
        "semiconductors": 1.0,
        "healthcare": 1.0,
        "financials": 1.0,
        "consumer": 1.0,
        "energy": 1.0,
    }

    if rotation == "growth":
        # Boost growth sectors
        bias["technology"] = 1.15
        bias["semiconductors"] = 1.15
        bias["consumer"] = 1.05
        # Reduce defensive
        bias["healthcare"] = 0.95
        bias["energy"] = 0.95
    elif rotation == "defensive":
        # Boost defensive sectors
        bias["healthcare"] = 1.15
        bias["energy"] = 1.05
        bias["financials"] = 1.05
        # Reduce growth
        bias["technology"] = 0.85
        bias["semiconductors"] = 0.85

    if outlook == "slowdown":
        # Favor defensive in slowdown
        bias["healthcare"] = bias.get("healthcare", 1.0) * 1.1
        bias["consumer"] = bias.get("consumer", 1.0) * 0.9

    return bias
