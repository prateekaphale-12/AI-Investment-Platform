from __future__ import annotations

from typing import Any, Literal

Risk = Literal["low", "medium", "high"]


def _risk_score_from(beta: float | None, signal: str) -> float:
    base = 40.0
    if beta is not None:
        base = min(100.0, max(10.0, 30.0 + beta * 25.0))
    if signal == "bullish":
        base -= 5
    elif signal == "bearish":
        base += 10
    return round(base, 1)


def _expected_return_heuristic(ytd_return_pct: float, signal: str) -> float:
    """Scaled trailing momentum proxy — not a forecast."""
    raw = ytd_return_pct * 0.35
    if signal == "bullish":
        raw += 2.0
    elif signal == "bearish":
        raw -= 2.0
    return round(max(-15.0, min(25.0, raw)), 2)


def build_allocations(
    budget: float,
    risk_tolerance: Risk,
    tickers_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    tickers_data items: ticker, market row, technical row, sentiment row, rationale partial (no summary).
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

    n = len(tickers_data)
    base_w = 100.0 / n
    weights: list[float] = []
    for row in tickers_data:
        sig = (row.get("technical") or {}).get("signal") or "neutral"
        w = base_w
        if risk_tolerance == "low" and sig == "bearish":
            w *= 0.85
        elif risk_tolerance == "high" and sig == "bullish":
            w *= 1.1
        elif sig == "bullish":
            w *= 1.05
        elif sig == "bearish":
            w *= 0.9
        weights.append(w)
    s = sum(weights)
    weights = [w / s * 100.0 for w in weights]

    allocations: list[dict[str, Any]] = []
    exp_returns: list[float] = []
    for w, row in zip(weights, tickers_data, strict=True):
        t = row["ticker"]
        m = row.get("market") or {}
        tech = row.get("technical") or {}
        sent = row.get("sentiment") or {}
        info = (m.get("info") or {}) if isinstance(m.get("info"), dict) else {}
        beta = info.get("beta")
        ytd = float(m.get("ytd_return_pct") or 0.0)
        sig = tech.get("signal") or "neutral"
        er = _expected_return_heuristic(ytd, sig)
        exp_returns.append(er * (w / 100.0))
        risk_s = _risk_score_from(beta if isinstance(beta, int | float) else None, sig)
        rationale = row.get("rationale") or {}
        allocations.append(
            {
                "ticker": t,
                "allocation_pct": round(w, 2),
                "amount": round(budget * w / 100.0, 2),
                "expected_return": er,
                "risk_score": risk_s,
                "rationale": rationale,
            }
        )

    total_er = round(sum(exp_returns), 2)
    best = max(tickers_data, key=lambda r: float((r.get("market") or {}).get("ytd_return_pct") or 0.0))
    div_score = min(100.0, 50.0 + n * 8.0)

    summary = {
        "total_budget": budget,
        "total_expected_return": total_er,
        "overall_risk": risk_tolerance,
        "diversification_score": round(div_score, 1),
        "best_performer": best.get("ticker"),
        "recommended_action": "Research & due diligence only — not investment advice.",
    }
    return allocations, summary
