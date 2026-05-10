from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import aiosqlite
import pandas as pd
import yfinance as yf
from loguru import logger

CACHE_TTL = timedelta(hours=1)


async def _cache_get(db: aiosqlite.Connection, ticker: str, data_type: str) -> dict[str, Any] | None:
    cur = await db.execute(
        "SELECT data, fetched_at FROM stock_cache WHERE ticker = ? AND data_type = ?",
        (ticker.upper(), data_type),
    )
    row = await cur.fetchone()
    if not row:
        return None
    fetched = datetime.fromisoformat(row["fetched_at"])
    if datetime.now(UTC).replace(tzinfo=None) - fetched > CACHE_TTL:
        return None
    return json.loads(row["data"])


async def _cache_set(db: aiosqlite.Connection, ticker: str, data_type: str, data: dict[str, Any]) -> None:
    await db.execute(
        """
        INSERT INTO stock_cache (ticker, data_type, data, fetched_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ticker, data_type) DO UPDATE SET
            data = excluded.data,
            fetched_at = excluded.fetched_at
        """,
        (ticker.upper(), data_type, json.dumps(data), datetime.now(UTC).replace(tzinfo=None).isoformat()),
    )


def _yf_history_sync(ticker: str, period: str = "1y") -> pd.DataFrame:
    t = yf.Ticker(ticker)
    return t.history(period=period, auto_adjust=True)


def _yf_info_sync(ticker: str) -> dict[str, Any]:
    t = yf.Ticker(ticker)
    info = t.info or {}
    return dict(info)


async def fetch_price_history(db: aiosqlite.Connection | None, ticker: str, period: str = "1y") -> pd.DataFrame:
    ticker = ticker.upper()
    cached: dict[str, Any] | None = None
    if db:
        cached = await _cache_get(db, ticker, "price_" + period)
    if cached and cached.get("records"):
        return pd.DataFrame(cached["records"])
    df = await asyncio.to_thread(_yf_history_sync, ticker, period)
    out = pd.DataFrame()
    try:
        if df is None or df.empty:
            logger.warning("No price history for {}", ticker)
        else:
            out = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            out = out.reset_index()
            if "Date" in out.columns:
                out = out.rename(columns={"Date": "date"})
            elif "index" in out.columns:
                out = out.rename(columns={"index": "date"})
            records = []
            for idx, row in out.iterrows():
                date_value = row.get("date")
                if hasattr(date_value, "isoformat"):
                    date_iso = date_value.isoformat()
                else:
                    date_iso = str(date_value)
                rec = {"date": date_iso}
                for k in out.columns:
                    if k == "date":
                        continue
                    rec[k] = float(row[k])
                records.append(rec)
            if db:
                await _cache_set(db, ticker, "price_" + period, {"records": records})
    except Exception as e:
        logger.exception("fetch_price_history {}: {}", ticker, e)
        raise
    return out


async def fetch_stock_info(db: aiosqlite.Connection | None, ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    if db:
        hit = await _cache_get(db, ticker, "info")
        if hit:
            return hit
    raw = await asyncio.to_thread(_yf_info_sync, ticker)
    simplified = {
        "symbol": ticker,
        "shortName": raw.get("shortName") or raw.get("longName"),
        "sector": raw.get("sector"),
        "industry": raw.get("industry"),
        "beta": raw.get("beta"),
        "trailingPE": raw.get("trailingPE"),
        "forwardPE": raw.get("forwardPE"),
        "profitMargins": raw.get("profitMargins"),
        "revenueGrowth": raw.get("revenueGrowth"),
        "marketCap": raw.get("marketCap"),
        "averageAnalystRating": raw.get("averageAnalystRating"),
        "numberOfAnalystOpinions": raw.get("numberOfAnalystOpinions"),
    }
    if db:
        await _cache_set(db, ticker, "info", simplified)
    return simplified


async def build_market_row(
    db: aiosqlite.Connection | None,
    ticker: str,
) -> dict[str, Any]:
    ticker = ticker.upper()
    try:
        df = await fetch_price_history(db, ticker, "1y")
        info = await fetch_stock_info(db, ticker)
        last_close = float(df["Close"].iloc[-1]) if df is not None and not df.empty else None
        first_close = float(df["Close"].iloc[0]) if df is not None and len(df) > 1 else last_close
        ytd_return_pct = (
            round((last_close / first_close - 1.0) * 100.0, 2)
            if last_close and first_close
            else 0.0
        )
        return {
            "ticker": ticker,
            "current_price": last_close,
            "ytd_return_pct": ytd_return_pct,
            "info": info,
        }
    except Exception as e:
        logger.warning("build_market_row failed {}: {}", ticker, e)
        return {"ticker": ticker, "error": str(e)}
