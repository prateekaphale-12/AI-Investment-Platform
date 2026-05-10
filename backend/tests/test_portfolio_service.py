from app.services.portfolio_service import build_allocations


def _row(ticker: str, ytd: float, signal: str, beta: float) -> dict:
    return {
        "ticker": ticker,
        "market": {"ytd_return_pct": ytd, "info": {"beta": beta}},
        "technical": {"signal": signal},
        "sentiment": {},
        "rationale": {"market_trend": "x", "technical": "y"},
    }


def test_build_allocations_sums_to_100_and_budget_amount() -> None:
    data = [
        _row("AAA", 20.0, "bullish", 1.1),
        _row("BBB", 10.0, "neutral", 0.9),
        _row("CCC", -5.0, "bearish", 1.4),
    ]
    allocations, summary = build_allocations(50000, "medium", data)

    assert len(allocations) == 3
    total_pct = sum(a["allocation_pct"] for a in allocations)
    total_amt = sum(a["amount"] for a in allocations)

    assert abs(total_pct - 100.0) < 0.2
    assert abs(total_amt - 50000.0) < 2.0
    assert summary["overall_risk"] == "medium"
    assert summary["best_performer"] == "AAA"


def test_build_allocations_empty_input() -> None:
    allocations, summary = build_allocations(10000, "low", [])
    assert allocations == []
    assert summary["total_expected_return"] == 0.0
