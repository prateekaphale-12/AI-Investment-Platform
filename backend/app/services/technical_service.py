from __future__ import annotations

from typing import Any

import pandas as pd
from loguru import logger


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta.where(delta < 0, 0.0))
    avg_gain = gains.rolling(length, min_periods=length).mean()
    avg_loss = losses.rolling(length, min_periods=length).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    # Edge cases: strictly rising windows have zero losses => RSI should be 100.
    rsi = rsi.where(avg_loss != 0, 100.0)
    # Strictly falling windows with zero gains => RSI should be 0.
    rsi = rsi.where(avg_gain != 0, 0.0)
    return rsi


def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series]:
    ef = _ema(series, fast)
    es = _ema(series, slow)
    line = ef - es
    sig = _ema(line, signal)
    return line, sig


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()


def _signal_from(rsi: float | None, macd: float | None, macd_sig: float | None, price: float, sma50: float | None) -> str:
    if rsi is None:
        return "neutral"
    if rsi > 70:
        return "bearish"
    if rsi < 30:
        return "bullish"
    if macd is not None and macd_sig is not None and macd > macd_sig and price and sma50 and price > sma50:
        return "bullish"
    if macd is not None and macd_sig is not None and macd < macd_sig:
        return "bearish"
    return "neutral"


def compute_indicators(price_df: pd.DataFrame) -> dict[str, Any]:
    if price_df is None or price_df.empty or "Close" not in price_df.columns:
        return {"signal": "neutral", "error": "insufficient price data"}
    close = price_df["Close"].astype(float)
    try:
        rsi_s = _rsi(close, 14)
        macd_line, macd_sig_s = _macd(close, 12, 26, 9)
        sma20 = _sma(close, 20)
        sma50 = _sma(close, 50)
        sma200 = _sma(close, 200)
        last = float(close.iloc[-1])
        rsi_last = float(rsi_s.dropna().iloc[-1]) if not rsi_s.dropna().empty else None
        macd_last = float(macd_line.dropna().iloc[-1]) if not macd_line.dropna().empty else None
        macd_sig_last = float(macd_sig_s.dropna().iloc[-1]) if not macd_sig_s.dropna().empty else None
        sma20_v = float(sma20.dropna().iloc[-1]) if not sma20.dropna().empty else None
        sma50_v = float(sma50.dropna().iloc[-1]) if not sma50.dropna().empty else None
        sma200_v = float(sma200.dropna().iloc[-1]) if not sma200.dropna().empty else None
        sig = _signal_from(rsi_last, macd_last, macd_sig_last, last, sma50_v)
        return {
            "current_price": last,
            "rsi": rsi_last,
            "macd": macd_last,
            "macd_signal": macd_sig_last,
            "sma_20": sma20_v,
            "sma_50": sma50_v,
            "sma_200": sma200_v,
            "signal": sig,
        }
    except Exception as e:
        logger.warning("compute_indicators: {}", e)
        return {"signal": "neutral", "error": str(e)}
