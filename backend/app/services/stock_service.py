from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf
from loguru import logger

from app.services.redis_service import cache_get_json, cache_set_json

CACHE_TTL = timedelta(hours=1)


async def _cache_get(db: Any, ticker: str, data_type: str) -> dict[str, Any] | None:
    cur = await db.execute(
        "SELECT data, fetched_at FROM stock_cache WHERE ticker = ? AND data_type = ?",
        (ticker.upper(), data_type),
    )
    row = await cur.fetchone()
    if not row:
        return None
    
    # row["fetched_at"] is a naive datetime from DB (no timezone info)
    fetched = row["fetched_at"]
    
    # Compare naive datetimes to avoid timezone mismatch errors
    if datetime.now(UTC).replace(tzinfo=None) - fetched > CACHE_TTL:
        return None
    return json.loads(row["data"])


async def _cache_set(db: Any, ticker: str, data_type: str, data: dict[str, Any]) -> None:
    # Use naive UTC datetime for PostgreSQL (remove tzinfo before storing)
    # This ensures consistency with what comes back from the DB
    now = datetime.now(UTC).replace(tzinfo=None)
    
    await db.execute(
        """
        INSERT INTO stock_cache (ticker, data_type, data, fetched_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ticker, data_type) DO UPDATE SET
            data = excluded.data,
            fetched_at = excluded.fetched_at
        """,
        (ticker.upper(), data_type, json.dumps(data), now),
    )


def _yf_history_sync(ticker: str, period: str = "1y") -> pd.DataFrame:
    t = yf.Ticker(ticker)
    return t.history(period=period, auto_adjust=True)


def _yf_info_sync(ticker: str) -> dict[str, Any]:
    t = yf.Ticker(ticker)
    info = t.info or {}
    
    # Get additional data
    try:
        recommendations = t.recommendations
        insider_transactions = t.insider_transactions
        institutional_holders = t.institutional_holders
    except Exception:
        recommendations = None
        insider_transactions = None
        institutional_holders = None
    
    return {
        "info": dict(info),
        "recommendations": recommendations,
        "insider_transactions": insider_transactions,
        "institutional_holders": institutional_holders,
    }


async def fetch_price_history(db: Any | None, ticker: str, period: str = "1y") -> pd.DataFrame:
    ticker = ticker.upper()
    redis_key = f"stock:{ticker}:price:{period}"
    redis_cached = await cache_get_json(redis_key)
    if redis_cached and redis_cached.get("records"):
        return pd.DataFrame(redis_cached["records"])
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
            await cache_set_json(redis_key, {"records": records}, ttl_seconds=3600)
    except Exception as e:
        logger.exception("fetch_price_history {}: {}", ticker, e)
        raise
    return out


async def fetch_stock_info(db: Any | None, ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    redis_key = f"stock:{ticker}:info"
    redis_hit = await cache_get_json(redis_key)
    if redis_hit:
        return redis_hit
    if db:
        hit = await _cache_get(db, ticker, "info")
        if hit:
            return hit
    
    data = await asyncio.to_thread(_yf_info_sync, ticker)
    raw = data.get("info", {})
    recommendations = data.get("recommendations")
    insider_transactions = data.get("insider_transactions")
    institutional_holders = data.get("institutional_holders")
    
    # Enhanced fundamental data
    simplified = {
        "symbol": ticker,
        "shortName": raw.get("shortName") or raw.get("longName"),
        "sector": raw.get("sector"),
        "industry": raw.get("industry"),
        
        # Valuation metrics
        "beta": raw.get("beta"),
        "trailingPE": raw.get("trailingPE"),
        "forwardPE": raw.get("forwardPE"),
        "priceToBook": raw.get("priceToBook"),
        "priceToSales": raw.get("priceToSalesTrailing12Months"),
        "enterpriseToEbitda": raw.get("enterpriseToEbitda"),
        "pegRatio": raw.get("pegRatio"),
        
        # Profitability metrics
        "profitMargins": raw.get("profitMargins"),
        "operatingMargins": raw.get("operatingMargins"),
        "grossMargins": raw.get("grossMargins"),
        "returnOnEquity": raw.get("returnOnEquity"),
        "returnOnAssets": raw.get("returnOnAssets"),
        
        # Growth metrics
        "revenueGrowth": raw.get("revenueGrowth"),
        "earningsGrowth": raw.get("earningsGrowth"),
        "earningsQuarterlyGrowth": raw.get("earningsQuarterlyGrowth"),
        
        # Cash flow metrics
        "freeCashflow": raw.get("freeCashflow"),
        "operatingCashflow": raw.get("operatingCashflow"),
        
        # Debt metrics
        "debtToEquity": raw.get("debtToEquity"),
        "currentRatio": raw.get("currentRatio"),
        "quickRatio": raw.get("quickRatio"),
        "totalDebt": raw.get("totalDebt"),
        "totalCash": raw.get("totalCash"),
        
        # Market metrics
        "marketCap": raw.get("marketCap"),
        "enterpriseValue": raw.get("enterpriseValue"),
        "sharesOutstanding": raw.get("sharesOutstanding"),
        "floatShares": raw.get("floatShares"),
        "sharesShort": raw.get("sharesShort"),
        "shortRatio": raw.get("shortRatio"),
        "shortPercentOfFloat": raw.get("shortPercentOfFloat"),
        
        # Analyst data
        "averageAnalystRating": raw.get("averageAnalystRating"),
        "numberOfAnalystOpinions": raw.get("numberOfAnalystOpinions"),
        "targetHighPrice": raw.get("targetHighPrice"),
        "targetLowPrice": raw.get("targetLowPrice"),
        "targetMeanPrice": raw.get("targetMeanPrice"),
        "targetMedianPrice": raw.get("targetMedianPrice"),
        
        # Dividend data
        "dividendRate": raw.get("dividendRate"),
        "dividendYield": raw.get("dividendYield"),
        "payoutRatio": raw.get("payoutRatio"),
        
        # Insider/Institutional
        "heldPercentInsiders": raw.get("heldPercentInsiders"),
        "heldPercentInstitutions": raw.get("heldPercentInstitutions"),
    }
    
    # Process analyst recommendations
    if recommendations is not None and not recommendations.empty:
        try:
            recent_recs = recommendations.tail(20)  # Last 20 recommendations
            simplified["analyst_recommendations"] = {
                "strongBuy": int(recent_recs["strongBuy"].sum()) if "strongBuy" in recent_recs else 0,
                "buy": int(recent_recs["buy"].sum()) if "buy" in recent_recs else 0,
                "hold": int(recent_recs["hold"].sum()) if "hold" in recent_recs else 0,
                "sell": int(recent_recs["sell"].sum()) if "sell" in recent_recs else 0,
                "strongSell": int(recent_recs["strongSell"].sum()) if "strongSell" in recent_recs else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to process recommendations for {ticker}: {e}")
            simplified["analyst_recommendations"] = None
    else:
        simplified["analyst_recommendations"] = None
    
    # Process insider transactions (last 90 days)
    if insider_transactions is not None and not insider_transactions.empty:
        try:
            cutoff_date = datetime.now() - timedelta(days=90)
            recent_insider = insider_transactions[
                pd.to_datetime(insider_transactions["Start Date"]) > cutoff_date
            ]
            
            buys = recent_insider[recent_insider["Transaction"].str.contains("Buy", case=False, na=False)]
            sells = recent_insider[recent_insider["Transaction"].str.contains("Sale", case=False, na=False)]
            
            buy_shares = buys["Shares"].sum() if not buys.empty else 0
            sell_shares = sells["Shares"].sum() if not sells.empty else 0
            
            simplified["insider_activity"] = {
                "buy_transactions": len(buys),
                "sell_transactions": len(sells),
                "net_shares": int(buy_shares - sell_shares),
                "sentiment": "bullish" if buy_shares > sell_shares else "bearish" if sell_shares > buy_shares else "neutral",
            }
        except Exception as e:
            logger.warning(f"Failed to process insider transactions for {ticker}: {e}")
            simplified["insider_activity"] = None
    else:
        simplified["insider_activity"] = None
    
    # Process institutional holders
    if institutional_holders is not None and not institutional_holders.empty:
        try:
            simplified["institutional_ownership"] = {
                "total_holders": len(institutional_holders),
                "top_5_ownership_pct": float(institutional_holders.head(5)["% Out"].sum()) if "% Out" in institutional_holders else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to process institutional holders for {ticker}: {e}")
            simplified["institutional_ownership"] = None
    else:
        simplified["institutional_ownership"] = None
    
    if db:
        await _cache_set(db, ticker, "info", simplified)
    await cache_set_json(redis_key, simplified, ttl_seconds=3600)
    return simplified


async def build_market_row(
    db: Any | None,
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



async def fetch_financial_trends(db: Any | None, ticker: str) -> dict[str, Any]:
    """
    Analyze financial statement trends (revenue, earnings, margins).
    
    Returns trends over last 4 quarters.
    """
    ticker = ticker.upper()
    redis_key = f"stock:{ticker}:trends"
    redis_hit = await cache_get_json(redis_key)
    if redis_hit:
        return redis_hit
    
    if db:
        hit = await _cache_get(db, ticker, "trends")
        if hit:
            return hit
    
    try:
        t = yf.Ticker(ticker)
        
        # Get quarterly financials
        income_stmt = await asyncio.to_thread(lambda: t.quarterly_income_stmt)
        balance_sheet = await asyncio.to_thread(lambda: t.quarterly_balance_sheet)
        cash_flow = await asyncio.to_thread(lambda: t.quarterly_cashflow)
        
        trends = {}
        
        # Revenue trend
        if income_stmt is not None and not income_stmt.empty and "Total Revenue" in income_stmt.index:
            revenue_series = income_stmt.loc["Total Revenue"].dropna()
            if len(revenue_series) >= 2:
                trends["revenue_trend"] = _calculate_trend(revenue_series)
                trends["revenue_growth_qoq"] = _calculate_qoq_growth(revenue_series)
        
        # Earnings trend
        if income_stmt is not None and not income_stmt.empty and "Net Income" in income_stmt.index:
            earnings_series = income_stmt.loc["Net Income"].dropna()
            if len(earnings_series) >= 2:
                trends["earnings_trend"] = _calculate_trend(earnings_series)
                trends["earnings_growth_qoq"] = _calculate_qoq_growth(earnings_series)
        
        # Margin trends
        if income_stmt is not None and not income_stmt.empty:
            if "Total Revenue" in income_stmt.index and "Gross Profit" in income_stmt.index:
                revenue = income_stmt.loc["Total Revenue"]
                gross_profit = income_stmt.loc["Gross Profit"]
                gross_margins = (gross_profit / revenue * 100).dropna()
                if len(gross_margins) >= 2:
                    trends["gross_margin_trend"] = _calculate_trend(gross_margins)
            
            if "Total Revenue" in income_stmt.index and "Operating Income" in income_stmt.index:
                revenue = income_stmt.loc["Total Revenue"]
                operating_income = income_stmt.loc["Operating Income"]
                operating_margins = (operating_income / revenue * 100).dropna()
                if len(operating_margins) >= 2:
                    trends["operating_margin_trend"] = _calculate_trend(operating_margins)
        
        # Cash flow trend
        if cash_flow is not None and not cash_flow.empty and "Operating Cash Flow" in cash_flow.index:
            ocf_series = cash_flow.loc["Operating Cash Flow"].dropna()
            if len(ocf_series) >= 2:
                trends["cash_flow_trend"] = _calculate_trend(ocf_series)
        
        # Debt trend
        if balance_sheet is not None and not balance_sheet.empty and "Total Debt" in balance_sheet.index:
            debt_series = balance_sheet.loc["Total Debt"].dropna()
            if len(debt_series) >= 2:
                trends["debt_trend"] = _calculate_trend(debt_series)
        
        if db:
            await _cache_set(db, ticker, "trends", trends)
        await cache_set_json(redis_key, trends, ttl_seconds=3600)
        
        return trends
    except Exception as e:
        logger.warning(f"Failed to fetch financial trends for {ticker}: {e}")
        return {}


def _calculate_trend(series: pd.Series) -> str:
    """
    Calculate trend direction from a pandas Series.
    
    Returns: "improving", "stable", "declining"
    """
    if len(series) < 2:
        return "unknown"
    
    # Get last 4 values (or all if less than 4)
    values = series.head(min(4, len(series))).tolist()
    
    # Calculate average change
    changes = []
    for i in range(len(values) - 1):
        if values[i+1] != 0:
            change = (values[i] - values[i+1]) / abs(values[i+1])
            changes.append(change)
    
    if not changes:
        return "stable"
    
    avg_change = sum(changes) / len(changes)
    
    if avg_change > 0.05:  # >5% average growth
        return "improving"
    elif avg_change < -0.05:  # >5% average decline
        return "declining"
    else:
        return "stable"


def _calculate_qoq_growth(series: pd.Series) -> float:
    """Calculate quarter-over-quarter growth rate"""
    if len(series) < 2:
        return 0.0
    
    latest = series.iloc[0]
    previous = series.iloc[1]
    
    if previous == 0:
        return 0.0
    
    return round((latest - previous) / abs(previous) * 100, 2)
