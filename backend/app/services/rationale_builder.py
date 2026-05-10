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
    rsi = tech.get("rsi")
    sig = tech.get("signal")
    macd = tech.get("macd")
    msig = tech.get("macd_signal")
    parts = []
    if rsi is not None:
        parts.append(f"RSI(14) {round(rsi, 1)}")
    if macd is not None and msig is not None:
        parts.append(f"MACD vs signal: {round(macd, 3)} / {round(msig, 3)}")
    parts.append(f"Signal: {sig or 'neutral'}")
    return "; ".join(parts) if parts else "No technical metrics available."


def describe_sentiment(sent: dict[str, Any]) -> str:
    lab = sent.get("label")
    comp = sent.get("compound")
    n = sent.get("headlines_used", 0)
    if not n:
        return "No recent headlines available for sentiment scoring."
    return f"VADER-style aggregate {comp} ({lab}) from {n} headline(s)."


def describe_fundamentals(info: dict[str, Any]) -> str:
    pe = info.get("trailingPE")
    rg = info.get("revenueGrowth")
    pm = info.get("profitMargins")
    parts = []
    if pe is not None and isinstance(pe, int | float):
        parts.append(f"Trailing P/E ~{round(float(pe), 1)}")
    if rg is not None and isinstance(rg, int | float):
        parts.append(f"Revenue growth ~{round(float(rg) * 100, 1)}%")
    if pm is not None and isinstance(pm, int | float):
        parts.append(f"Profit margin ~{round(float(pm) * 100, 1)}%")
    return "; ".join(parts) if parts else "Fundamental fields limited in current data pull."


def describe_risk(info: dict[str, Any], tech: dict[str, Any]) -> str:
    beta = info.get("beta")
    btxt = f"Beta ~{round(float(beta), 2)}" if isinstance(beta, int | float) else "Beta unavailable"
    sig = tech.get("signal") or "neutral"
    return f"{btxt}; technical stance {sig}."
