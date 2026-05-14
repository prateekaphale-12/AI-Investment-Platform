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


def _signal_from(
    rsi: float | None,
    macd: float | None,
    macd_sig: float | None,
    price: float,
    sma50: float | None,
    sma200: float | None = None,
) -> dict[str, Any]:
    """
    Generate institutional-grade technical signal with nuance.
    
    Returns structured analysis instead of binary label:
    {
        "signal": "bullish" | "bearish" | "mixed" | "bullish_but_extended" | "bearish_but_oversold" | "neutral",
        "trend": "bullish" | "bearish",
        "momentum": "bullish" | "bearish",
        "extension": "strongly_overbought" | "moderately_overbought" | "neutral" | "moderately_oversold" | "strongly_oversold",
        "confidence": 0.0-1.0,
        "long_term_trend": "bullish" | "bearish" | "unknown"
    }
    
    Key insights:
    - RSI > 70 is NOT bearish; it's overbought (elevated pullback risk)
    - RSI < 30 is NOT bullish; it's oversold (bounce potential)
    - Trend and momentum are independent
    - Overbought in uptrend = continuation risk, not reversal signal
    - Oversold in downtrend = continuation risk, not bounce signal
    """
    if None in (rsi, macd, macd_sig, sma50):
        return {
            "signal": "neutral",
            "trend": "unknown",
            "momentum": "unknown",
            "extension": "unknown",
            "confidence": 0.3,
            "long_term_trend": "unknown",
        }
    
    # Momentum: MACD crossover
    macd_bullish = macd > macd_sig
    
    # Trend: Price vs SMA50
    trend_bullish = price > sma50
    
    # Long-term trend: Price vs SMA200
    long_term_bullish = sma200 is not None and price > sma200
    
    # Extension: RSI interpretation
    if rsi >= 75:
        extension = "strongly_overbought"
    elif rsi >= 65:
        extension = "moderately_overbought"
    elif rsi <= 25:
        extension = "strongly_oversold"
    elif rsi <= 35:
        extension = "moderately_oversold"
    else:
        extension = "neutral"
    
    # Final signal synthesis
    if macd_bullish and trend_bullish:
        signal = "bullish"
        if "overbought" in extension:
            signal = "bullish_but_extended"
    elif (not macd_bullish) and (not trend_bullish):
        signal = "bearish"
        if "oversold" in extension:
            signal = "bearish_but_oversold"
    else:
        signal = "mixed"
    
    # Confidence scoring
    confidence = 0.5
    
    # Agreement between momentum and trend increases confidence
    if macd_bullish == trend_bullish:
        confidence += 0.2
    
    # Long-term trend alignment increases confidence
    if long_term_bullish is not None:
        if (macd_bullish and long_term_bullish) or (not macd_bullish and not long_term_bullish):
            confidence += 0.15
    
    # Neutral extension increases confidence (no overextension)
    if extension == "neutral":
        confidence += 0.1
    
    return {
        "signal": signal,
        "trend": "bullish" if trend_bullish else "bearish",
        "momentum": "bullish" if macd_bullish else "bearish",
        "extension": extension,
        "confidence": round(min(confidence, 1.0), 2),
        "long_term_trend": "bullish" if long_term_bullish else ("bearish" if sma200 is not None else "unknown"),
    }


def compute_indicators(price_df: pd.DataFrame) -> dict[str, Any]:
    if price_df is None or price_df.empty or "Close" not in price_df.columns:
        return {
            "signal": "neutral",
            "trend": "unknown",
            "momentum": "unknown",
            "extension": "unknown",
            "confidence": 0.0,
            "error": "insufficient price data",
        }
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
        
        sig_dict = _signal_from(rsi_last, macd_last, macd_sig_last, last, sma50_v, sma200_v)
        
        return {
            "current_price": last,
            "rsi": rsi_last,
            "macd": macd_last,
            "macd_signal": macd_sig_last,
            "sma_20": sma20_v,
            "sma_50": sma50_v,
            "sma_200": sma200_v,
            **sig_dict,  # Unpack signal dict (signal, trend, momentum, extension, confidence, long_term_trend)
        }
    except Exception as e:
        logger.warning("compute_indicators: {}", e)
        return {
            "signal": "neutral",
            "trend": "unknown",
            "momentum": "unknown",
            "extension": "unknown",
            "confidence": 0.0,
            "error": str(e),
        }
