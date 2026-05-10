import pandas as pd

from app.services.technical_service import compute_indicators


def test_compute_indicators_with_uptrend_returns_expected_keys() -> None:
    close = [100 + i for i in range(240)]
    df = pd.DataFrame({"Close": close})

    out = compute_indicators(df)

    assert out["signal"] in {"bullish", "neutral", "bearish"}
    assert isinstance(out["current_price"], float)
    assert out["sma_20"] is not None
    assert out["sma_50"] is not None
    assert out["sma_200"] is not None
    assert out["rsi"] is not None


def test_compute_indicators_handles_empty_input() -> None:
    out = compute_indicators(pd.DataFrame())
    assert out["signal"] == "neutral"
    assert "error" in out
