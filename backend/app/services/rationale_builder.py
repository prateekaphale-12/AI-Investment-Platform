from __future__ import annotations

from typing import Any


def describe_market_trend(market: dict[str, Any]) -> str:
    ytd = market.get("ytd_return_pct")
    price = market.get("current_price")
    if ytd is None:
        return "Insufficient price history for trend summary."
    direction = "up" if ytd >= 0 else "down"
    return f"Trailing period return ~{ytd}% ({direction}); last price {price}."


def describe_technical(tech: dict[str, Any]) -> str:
    """
    Provide institutional-grade technical analysis with nuance.
    
    Describes:
    - Trend state (short-term and long-term)
    - Momentum direction
    - Extension state (overbought/oversold/neutral)
    - Confidence in the signal
    - Specific risks or opportunities
    """
    rsi = tech.get("rsi")
    macd = tech.get("macd")
    msig = tech.get("macd_signal")
    price = tech.get("current_price")
    sma50 = tech.get("sma_50")
    sma200 = tech.get("sma_200")
    
    # New structured signal fields
    trend = tech.get("trend", "unknown")
    momentum = tech.get("momentum", "unknown")
    extension = tech.get("extension", "unknown")
    confidence = tech.get("confidence", 0.0)
    long_term_trend = tech.get("long_term_trend", "unknown")
    signal = tech.get("signal", "neutral")
    
    parts = []
    
    # Trend analysis
    if trend != "unknown":
        parts.append(f"Short-term trend: {trend}")
    
    if long_term_trend != "unknown":
        parts.append(f"Long-term trend: {long_term_trend}")
    
    # Momentum analysis
    if momentum != "unknown":
        parts.append(f"Momentum: {momentum}")
    
    # RSI with context
    if rsi is not None:
        rsi_rounded = round(rsi, 1)
        parts.append(f"RSI(14) {rsi_rounded}")
    
    # MACD details
    if macd is not None and msig is not None:
        macd_rounded = round(macd, 3)
        msig_rounded = round(msig, 3)
        parts.append(f"MACD {macd_rounded} vs signal {msig_rounded}")
    
    # Extension state with risk/opportunity context
    if extension != "unknown":
        if extension == "strongly_overbought":
            parts.append(f"Extension: {extension} (elevated pullback risk)")
        elif extension == "moderately_overbought":
            parts.append(f"Extension: {extension} (some pullback risk)")
        elif extension == "strongly_oversold":
            parts.append(f"Extension: {extension} (bounce potential)")
        elif extension == "moderately_oversold":
            parts.append(f"Extension: {extension} (some bounce potential)")
        else:
            parts.append(f"Extension: {extension}")
    
    # Confidence score
    if confidence > 0:
        confidence_pct = round(confidence * 100)
        parts.append(f"Confidence: {confidence_pct}%")
    
    # Final signal interpretation
    if signal != "neutral":
        parts.append(f"Signal: {signal}")
    
    return "; ".join(parts) if parts else "No technical metrics available."


def describe_sentiment(sent: dict[str, Any]) -> str:
    lab = sent.get("label")
    comp = sent.get("compound")
    n = sent.get("headlines_used", 0)
    if not n:
        return "No recent headlines available for sentiment scoring."
    return f"VADER-style aggregate {comp} ({lab}) from {n} headline(s)."


def describe_fundamentals(info: dict[str, Any]) -> str:
    """
    Provide valuation-aware fundamental analysis.
    
    Includes:
    - P/E ratio with context (expensive/fair/cheap)
    - Revenue growth
    - Profit margin
    - PEG-like reasoning (growth vs valuation)
    """
    pe = info.get("trailingPE")
    rg = info.get("revenueGrowth")
    pm = info.get("profitMargins")
    parts = []
    
    if pe is not None and isinstance(pe, int | float):
        pe_rounded = round(float(pe), 1)
        # Valuation context
        if pe_rounded > 30:
            pe_context = "(expensive)"
        elif pe_rounded > 20:
            pe_context = "(fair)"
        else:
            pe_context = "(cheap)"
        parts.append(f"Trailing P/E ~{pe_rounded} {pe_context}")
    
    if rg is not None and isinstance(rg, int | float):
        rg_pct = round(float(rg) * 100, 1)
        parts.append(f"Revenue growth ~{rg_pct}%")
    
    if pm is not None and isinstance(pm, int | float):
        pm_pct = round(float(pm) * 100, 1)
        parts.append(f"Profit margin ~{pm_pct}%")
    
    # PEG-like reasoning: if growth is strong, higher P/E is justified
    if pe is not None and rg is not None:
        pe_float = float(pe)
        rg_pct = float(rg) * 100
        if rg_pct > 0:
            peg_proxy = pe_float / rg_pct
            if peg_proxy < 1.5:
                parts.append("(growth justifies valuation)")
            elif peg_proxy > 2.5:
                parts.append("(valuation premium vs growth)")
    
    return "; ".join(parts) if parts else "Fundamental fields limited in current data pull."


def describe_risk(info: dict[str, Any], tech: dict[str, Any]) -> str:
    """
    Provide nuanced risk assessment with confidence weighting.
    
    Includes:
    - Beta (systematic risk)
    - Technical stance with context
    - Volatility implications
    - Confidence in technical assessment
    """
    beta = info.get("beta")
    sig = tech.get("signal") or "neutral"
    rsi = tech.get("rsi")
    confidence = tech.get("confidence", 0.0)
    extension = tech.get("extension", "unknown")
    
    parts = []
    
    # Beta interpretation
    if isinstance(beta, int | float):
        beta_rounded = round(float(beta), 2)
        if beta_rounded > 1.2:
            beta_context = "(high volatility)"
        elif beta_rounded < 0.8:
            beta_context = "(low volatility)"
        else:
            beta_context = "(market-correlated)"
        parts.append(f"Beta ~{beta_rounded} {beta_context}")
    else:
        parts.append("Beta unavailable")
    
    # Technical stance with risk context
    if sig == "bullish":
        parts.append("technical stance bullish")
    elif sig == "bearish":
        parts.append("technical stance bearish")
    elif sig == "bullish_but_extended":
        parts.append("technical stance bullish but overextended")
    elif sig == "bearish_but_oversold":
        parts.append("technical stance bearish but oversold")
    else:
        parts.append("technical stance neutral/mixed")
    
    # Extension-based risk warning
    if extension == "strongly_overbought":
        parts.append("(strong pullback risk)")
    elif extension == "moderately_overbought":
        parts.append("(moderate pullback risk)")
    elif extension == "strongly_oversold":
        parts.append("(strong bounce potential)")
    elif extension == "moderately_oversold":
        parts.append("(moderate bounce potential)")
    
    # Confidence qualifier
    if confidence > 0:
        confidence_pct = round(confidence * 100)
        if confidence_pct >= 80:
            parts.append(f"(high confidence: {confidence_pct}%)")
        elif confidence_pct >= 60:
            parts.append(f"(moderate confidence: {confidence_pct}%)")
        else:
            parts.append(f"(low confidence: {confidence_pct}%)")
    
    return "; ".join(parts) + "."
