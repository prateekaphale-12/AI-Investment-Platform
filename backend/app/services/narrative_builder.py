"""
Narrative Builder - Converts internal technical signals into institutional-grade narratives.

This is the PRESENTATION LAYER that transforms:
- Internal: signal = "bullish_but_extended"
- External: "The stock remains in a strong upward trend, though recent gains may leave it vulnerable to short-term consolidation."

This is where the product becomes differentiated and premium.
"""

from __future__ import annotations

from typing import Any


def build_technical_narrative(tech: dict[str, Any]) -> str:
    """
    Convert technical signals into institutional-grade narrative.
    
    NOT: "Signal: bullish; RSI: 65; MACD: positive"
    BUT: "Momentum remains constructive, supported by continued strength above medium-term trend levels."
    """
    trend = tech.get("trend", "unknown")
    momentum = tech.get("momentum", "unknown")
    extension = tech.get("extension", "unknown")
    signal = tech.get("signal", "neutral")
    long_term_trend = tech.get("long_term_trend", "unknown")
    rsi = tech.get("rsi")
    confidence = tech.get("confidence", 0.0)

    # Build narrative based on signal type
    if signal == "bullish":
        narrative = _narrative_bullish(trend, momentum, extension, long_term_trend, rsi, confidence)
    elif signal == "bearish":
        narrative = _narrative_bearish(trend, momentum, extension, long_term_trend, rsi, confidence)
    elif signal == "bullish_but_extended":
        narrative = _narrative_bullish_extended(trend, momentum, extension, long_term_trend, rsi, confidence)
    elif signal == "bearish_but_oversold":
        narrative = _narrative_bearish_oversold(trend, momentum, extension, long_term_trend, rsi, confidence)
    elif signal == "mixed":
        narrative = _narrative_mixed(trend, momentum, extension, long_term_trend, rsi, confidence)
    else:
        narrative = _narrative_neutral(trend, momentum, extension, long_term_trend, rsi, confidence)

    return narrative


def _narrative_bullish(
    trend: str,
    momentum: str,
    extension: str,
    long_term_trend: str,
    rsi: float | None,
    confidence: float,
) -> str:
    """Narrative for bullish signal"""
    parts = []

    # Momentum quality
    if momentum == "bullish":
        parts.append("Momentum remains constructive")
    else:
        parts.append("Momentum shows mixed signals")

    # Trend alignment
    if trend == "bullish" and long_term_trend == "bullish":
        parts.append("supported by aligned short and long-term trend strength")
    elif trend == "bullish":
        parts.append("with near-term strength evident")
    else:
        parts.append("despite some near-term consolidation")

    # Extension context
    if extension == "neutral":
        parts.append("Price action remains balanced")
    elif "overbought" in extension:
        parts.append("though recent gains suggest elevated short-term pullback risk")
    elif "oversold" in extension:
        parts.append("with potential for further upside if oversold conditions resolve")

    # Confidence qualifier
    if confidence >= 0.55:
        parts.append("Technical setup appears favorable")
    else:
        parts.append("though conviction remains moderate")

    return ", ".join(parts) + "."


def _narrative_bearish(
    trend: str,
    momentum: str,
    extension: str,
    long_term_trend: str,
    rsi: float | None,
    confidence: float,
) -> str:
    """Narrative for bearish signal"""
    parts = []

    # Momentum quality
    if momentum == "bearish":
        parts.append("Momentum continues to deteriorate")
    else:
        parts.append("Momentum shows weakness")

    # Trend alignment
    if trend == "bearish" and long_term_trend == "bearish":
        parts.append("with both short and long-term trends pointing lower")
    elif trend == "bearish":
        parts.append("as near-term weakness persists")
    else:
        parts.append("despite some stabilization attempts")

    # Extension context
    if extension == "neutral":
        parts.append("Price structure remains vulnerable")
    elif "oversold" in extension:
        parts.append("though oversold conditions could support a temporary rebound")
    elif "overbought" in extension:
        parts.append("with further downside risk if support breaks")

    # Confidence qualifier
    if confidence >= 0.55:
        parts.append("Technical deterioration appears significant")
    else:
        parts.append("though conviction remains limited")

    return ", ".join(parts) + "."


def _narrative_bullish_extended(
    trend: str,
    momentum: str,
    extension: str,
    long_term_trend: str,
    rsi: float | None,
    confidence: float,
) -> str:
    """Narrative for bullish but extended signal"""
    parts = []

    parts.append("The stock remains in a strong upward trend")

    # Momentum quality
    if momentum == "bullish":
        parts.append("with momentum still constructive")
    else:
        parts.append("though momentum is beginning to show signs of fatigue")

    # Extension risk
    if "strongly_overbought" in extension:
        parts.append("Recent price acceleration suggests elevated short-term pullback risk")
    elif "moderately_overbought" in extension:
        parts.append("Recent gains may leave it vulnerable to near-term consolidation")
    else:
        parts.append("though recent gains may warrant caution")

    # Long-term context
    if long_term_trend == "bullish":
        parts.append("The longer-term trend remains supportive of further upside")
    else:
        parts.append("though longer-term trend context is mixed")

    return "; ".join(parts) + "."


def _narrative_bearish_oversold(
    trend: str,
    momentum: str,
    extension: str,
    long_term_trend: str,
    rsi: float | None,
    confidence: float,
) -> str:
    """Narrative for bearish but oversold signal"""
    parts = []

    parts.append("Downward momentum remains dominant")

    # Oversold opportunity
    if "strongly_oversold" in extension:
        parts.append("Oversold conditions could support a meaningful rebound")
    elif "moderately_oversold" in extension:
        parts.append("Oversold conditions may provide a temporary bounce opportunity")
    else:
        parts.append("though technical extremes could attract value buyers")

    # Trend context
    if trend == "bearish":
        parts.append("The near-term trend remains negative")
    else:
        parts.append("despite some stabilization in price action")

    # Long-term perspective
    if long_term_trend == "bullish":
        parts.append("Longer-term trend remains constructive, suggesting potential mean reversion")
    else:
        parts.append("with longer-term trend also showing weakness")

    return "; ".join(parts) + "."


def _narrative_mixed(
    trend: str,
    momentum: str,
    extension: str,
    long_term_trend: str,
    rsi: float | None,
    confidence: float,
) -> str:
    """Narrative for mixed signal"""
    parts = []

    parts.append("Technical indicators present conflicting signals")

    # Trend vs momentum
    if trend != momentum:
        parts.append(f"Near-term trend shows {trend} characteristics while momentum appears {momentum}")
    else:
        parts.append("with neither clear directional bias emerging")

    # Extension state
    if extension != "neutral":
        parts.append(f"Current extension state ({extension}) adds to the ambiguity")

    # Recommendation
    parts.append("Awaiting clearer technical confirmation before committing to a directional view")

    return "; ".join(parts) + "."


def _narrative_neutral(
    trend: str,
    momentum: str,
    extension: str,
    long_term_trend: str,
    rsi: float | None,
    confidence: float,
) -> str:
    """Narrative for neutral signal"""
    parts = []

    parts.append("Technical structure remains neutral")

    if trend == "neutral" and momentum == "neutral":
        parts.append("with neither clear directional bias in near-term price action")
    elif trend == "neutral":
        parts.append("despite some momentum signals")
    else:
        parts.append("with trend structure still consolidating")

    # Extension context
    if extension == "neutral":
        parts.append("Price levels appear balanced")
    else:
        parts.append(f"Current extension state ({extension}) suggests potential for directional movement")

    # Long-term context
    if long_term_trend != "neutral":
        parts.append(f"Longer-term trend remains {long_term_trend}, providing context for potential breakout direction")

    return "; ".join(parts) + "."


def build_sentiment_narrative(sent: dict[str, Any]) -> str:
    """
    Convert sentiment data into institutional narrative.
    
    NOT: "VADER aggregate 0.15 (positive) from 5 headlines"
    BUT: "Recent headlines show constructive tone with focus on earnings strength and AI initiatives."
    """
    label = sent.get("label", "neutral")
    consistency = sent.get("sentiment_consistency", 0.0)
    event_types = sent.get("event_types", [])
    headlines_used = sent.get("headlines_used", 0)
    compound = sent.get("compound", 0.0)

    if headlines_used == 0:
        return "Insufficient recent headline data for sentiment assessment."

    # Build narrative based on label and consistency
    if label == "positive":
        narrative = _sentiment_positive(consistency, event_types, headlines_used, compound)
    elif label == "negative":
        narrative = _sentiment_negative(consistency, event_types, headlines_used, compound)
    else:
        narrative = _sentiment_neutral(consistency, event_types, headlines_used, compound)

    return narrative


def _sentiment_positive(
    consistency: float,
    event_types: list[str],
    headlines_used: int,
    compound: float,
) -> str:
    """Narrative for positive sentiment"""
    parts = []

    # Consistency assessment
    if consistency >= 0.75:
        parts.append("Recent headlines show strong constructive tone")
    elif consistency >= 0.60:
        parts.append("Recent headlines generally show positive sentiment")
    else:
        parts.append("Recent headlines show mixed but slightly positive tone")

    # Event context
    if event_types:
        event_str = ", ".join(event_types)
        parts.append(f"with focus on {event_str}")

    # Data quality
    if headlines_used >= 8:
        parts.append(f"across {headlines_used} sources")
    elif headlines_used >= 5:
        parts.append(f"based on {headlines_used} recent articles")
    else:
        parts.append("though data is limited")

    return " ".join(parts) + "."


def _sentiment_negative(
    consistency: float,
    event_types: list[str],
    headlines_used: int,
    compound: float,
) -> str:
    """Narrative for negative sentiment"""
    parts = []

    # Consistency assessment
    if consistency >= 0.75:
        parts.append("Recent headlines show pronounced negative sentiment")
    elif consistency >= 0.60:
        parts.append("Recent headlines generally reflect concerns")
    else:
        parts.append("Recent headlines show mixed but slightly negative tone")

    # Event context
    if event_types:
        event_str = ", ".join(event_types)
        parts.append(f"centered on {event_str}")

    # Data quality
    if headlines_used >= 8:
        parts.append(f"across {headlines_used} sources")
    elif headlines_used >= 5:
        parts.append(f"based on {headlines_used} recent articles")
    else:
        parts.append("though data is limited")

    return " ".join(parts) + "."


def _sentiment_neutral(
    consistency: float,
    event_types: list[str],
    headlines_used: int,
    compound: float,
) -> str:
    """Narrative for neutral sentiment"""
    parts = []

    parts.append("Recent headlines show neutral to mixed sentiment")

    # Event context
    if event_types:
        event_str = ", ".join(event_types)
        parts.append(f"with coverage spanning {event_str}")

    # Data quality
    if headlines_used >= 8:
        parts.append(f"across {headlines_used} sources")
    elif headlines_used >= 5:
        parts.append(f"based on {headlines_used} recent articles")
    else:
        parts.append("though data is limited")

    return " ".join(parts) + "."


def build_fundamental_narrative(info: dict[str, Any], quality_score: float = 0.0) -> str:
    """
    Convert fundamental data into institutional narrative.
    
    Uses enhanced fundamental data: cash flow, debt, returns, analyst data, insider activity.
    
    NOT: "P/E 25.5; Revenue growth 15%; Margin 22%"
    BUT: "Valuation appears fair relative to growth trajectory, with strong cash generation and improving margins. Analysts maintain bullish stance with 15% upside to consensus target."
    """
    pe = info.get("trailingPE")
    rg = info.get("revenueGrowth")
    pm = info.get("profitMargins")
    roe = info.get("returnOnEquity")
    fcf = info.get("freeCashflow")
    debt_to_equity = info.get("debtToEquity")
    target_price = info.get("targetMeanPrice")
    current_price = info.get("currentPrice")
    analyst_recs = info.get("analyst_recommendations")
    insider_activity = info.get("insider_activity")

    if not any([pe, rg, pm]):
        return "Fundamental data limited in current dataset."

    parts = []

    # Valuation narrative (enhanced with PEG)
    if pe is not None and isinstance(pe, (int, float)):
        pe_float = float(pe)
        peg = info.get("pegRatio")
        
        if peg is not None and isinstance(peg, (int, float)) and float(peg) < 1.5:
            parts.append("Valuation appears attractive relative to growth")
        elif pe_float > 30:
            parts.append("Valuation appears elevated")
        elif pe_float > 20:
            parts.append("Valuation appears fair")
        else:
            parts.append("Valuation appears attractive")

    # Growth narrative (enhanced with earnings growth)
    if rg is not None and isinstance(rg, (int, float)):
        rg_pct = float(rg) * 100
        eg = info.get("earningsGrowth")
        
        if rg_pct > 20:
            growth_desc = "strong revenue growth trajectory"
        elif rg_pct > 10:
            growth_desc = "solid revenue growth"
        elif rg_pct > 0:
            growth_desc = "modest revenue growth"
        else:
            growth_desc = "slowing revenue growth"
        
        # Add earnings growth context
        if eg is not None and isinstance(eg, (int, float)):
            eg_pct = float(eg) * 100
            if eg_pct > rg_pct + 5:
                growth_desc += " with accelerating earnings"
            elif eg_pct < rg_pct - 5:
                growth_desc += " though earnings lag revenue"
        
        parts.append(f"with {growth_desc}")

    # Profitability narrative (enhanced with ROE and margins)
    if pm is not None and isinstance(pm, (int, float)):
        pm_pct = float(pm) * 100
        
        if pm_pct > 25:
            profit_desc = "Profit margins remain robust"
        elif pm_pct > 15:
            profit_desc = "Profit margins are healthy"
        else:
            profit_desc = "Profit margins warrant monitoring"
        
        # Add ROE context
        if roe is not None and isinstance(roe, (int, float)):
            roe_pct = float(roe) * 100
            if roe_pct > 20:
                profit_desc += ", with strong returns on equity"
            elif roe_pct > 15:
                profit_desc += ", with solid returns"
        
        parts.append(profit_desc)

    # Cash flow narrative (NEW)
    if fcf is not None and isinstance(fcf, (int, float)) and float(fcf) > 0:
        fcf_val = float(fcf)
        if fcf_val > 1e10:  # > $10B
            parts.append("Strong free cash flow generation supports capital returns")
        elif fcf_val > 1e9:  # > $1B
            parts.append("Solid cash generation")
        else:
            parts.append("Positive free cash flow")

    # Debt narrative (NEW)
    if debt_to_equity is not None and isinstance(debt_to_equity, (int, float)):
        de_ratio = float(debt_to_equity)
        if de_ratio > 100:
            parts.append("though elevated leverage warrants monitoring")
        elif de_ratio < 30:
            parts.append("Balance sheet remains conservative")

    # Analyst narrative (NEW)
    if target_price is not None and current_price is not None:
        try:
            target = float(target_price)
            current = float(current_price)
            upside = (target - current) / current * 100
            
            if upside > 20:
                parts.append(f"Analysts see significant upside ({upside:.0f}% to consensus target)")
            elif upside > 10:
                parts.append(f"Analysts maintain bullish stance ({upside:.0f}% upside)")
            elif upside < -10:
                parts.append(f"Analyst targets imply downside risk ({upside:.0f}%)")
        except (ValueError, ZeroDivisionError):
            pass

    # Analyst recommendations (NEW)
    if analyst_recs:
        buy_count = analyst_recs.get("strongBuy", 0) + analyst_recs.get("buy", 0)
        sell_count = analyst_recs.get("sell", 0) + analyst_recs.get("strongSell", 0)
        total = buy_count + analyst_recs.get("hold", 0) + sell_count
        
        if total > 0 and buy_count > sell_count * 2:
            parts.append(f"Analyst consensus leans bullish ({buy_count}/{total} buy ratings)")
        elif total > 0 and sell_count > buy_count * 2:
            parts.append(f"Analyst consensus leans bearish ({sell_count}/{total} sell ratings)")

    # Insider activity (NEW)
    if insider_activity:
        sentiment = insider_activity.get("sentiment", "neutral")
        net_shares = insider_activity.get("net_shares", 0)
        
        if sentiment == "bullish" and net_shares > 10000:
            parts.append("Insider buying signals management confidence")
        elif sentiment == "bearish" and net_shares < -10000:
            parts.append("Notable insider selling warrants attention")

    return ", ".join(parts) + "." if parts else "Fundamental profile appears balanced."


def build_risk_narrative(info: dict[str, Any], tech: dict[str, Any], confidence: float = 0.0) -> str:
    """
    Convert risk factors into institutional narrative.
    
    NOT: "Beta 1.2; Signal bearish; Risk score 65"
    BUT: "Elevated volatility combined with weakening momentum creates meaningful downside risk."
    """
    beta = info.get("beta")
    signal = tech.get("signal", "neutral")
    extension = tech.get("extension", "unknown")
    rsi = tech.get("rsi")

    parts = []

    # Volatility narrative
    if beta is not None and isinstance(beta, (int, float)):
        beta_float = float(beta)
        if beta_float > 1.2:
            parts.append("Elevated volatility")
        elif beta_float < 0.8:
            parts.append("Low volatility")
        else:
            parts.append("Market-correlated volatility")

    # Signal-based risk
    if signal == "bearish":
        parts.append("combined with weakening momentum")
        parts.append("creates meaningful downside risk")
    elif signal == "bullish_but_extended":
        parts.append("though recent gains suggest pullback risk")
    elif signal == "bearish_but_oversold":
        parts.append("though oversold conditions may limit further downside")
    elif signal == "mixed":
        parts.append("with conflicting signals creating uncertainty")

    # Extension-based risk
    if "strongly_overbought" in extension:
        parts.append("Current extension levels suggest elevated correction risk")
    elif "strongly_oversold" in extension:
        parts.append("Current oversold levels could support a rebound")

    # Confidence qualifier
    if confidence < 0.45:
        parts.append("Risk assessment carries limited conviction")
    elif confidence >= 0.65:
        parts.append("Risk profile appears clearly defined")

    return " ".join(parts) + "." if parts else "Risk profile appears balanced."
