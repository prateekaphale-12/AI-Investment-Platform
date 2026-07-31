from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from loguru import logger

from app.db.init_db import get_connection
from app.services.data_validator import validate_snapshot_data
from app.services.news_aggregator_service import get_news_aggregator
from app.services.stock_service import build_market_row
from app.utils.stock_universe import SECTOR_TICKERS
from app.utils.ticker_names import get_company_name

# In-memory cache for snapshot
_snapshot_cache = {
    "data": None,
    "timestamp": None,
    "cache_duration_minutes": 30,  # Refresh every 30 minutes for stock data
    # Note: yfinance is FREE with no rate limits, so we can refresh more frequently
    # 30-minute refresh = 1,920 calls/day (very respectful usage)
}


async def generate_daily_snapshot() -> dict:
    tickers = list(dict.fromkeys(sum(SECTOR_TICKERS.values(), [])))[:20]
    db = await get_connection()
    news_agg = get_news_aggregator()
    
    try:
        rows = []
        for t in tickers:
            row = await build_market_row(db, t)
            # Add company name to each row
            row["company_name"] = get_company_name(t)
            rows.append(row)
        
        # Include all rows with valid returns (don't filter by error - let validation happen later)
        valid = [r for r in rows if isinstance(r.get("ytd_return_pct"), (int, float))]
        
        if not valid:
            logger.warning(f"No valid rows after filtering. Total rows: {len(rows)}")
            for r in rows:
                if "error" in r:
                    logger.warning(f"  {r.get('ticker')}: {r.get('error')}")
        
        gainers = sorted(valid, key=lambda x: x.get("ytd_return_pct", 0), reverse=True)[:10]
        losers = sorted(valid, key=lambda x: x.get("ytd_return_pct", 0))[:10]
        picks = gainers[:5]
        
        logger.info(f"Snapshot: {len(valid)} valid rows, {len(picks)} picks, {len(gainers)} gainers, {len(losers)} losers")
        
        # Get news for top gainers
        top_news = {}
        for ticker in [p.get("ticker") for p in picks[:3]]:
            if ticker:
                top_news[ticker] = await news_agg.get_ticker_news(ticker, limit=3)
        
        # Get general market news
        market_news = await news_agg.get_market_news(limit=5)
        
        # Replace NaN values with 0 for JSON serialization
        import math
        for row_list in [picks, gainers, losers, valid]:
            for row in row_list:
                if isinstance(row.get("ytd_return_pct"), float) and math.isnan(row.get("ytd_return_pct")):
                    row["ytd_return_pct"] = 0.0
        
        metrics = {
            "universe_count": len(valid),
            "avg_return_pct": round(sum(r.get("ytd_return_pct", 0) for r in valid) / max(len(valid), 1), 2),
        }
        payload = {
            "snapshot_date": date.today().isoformat(),
            "picks": picks,
            "gainers": gainers,
            "losers": losers,
            "metrics": metrics,
            "top_news": top_news,
            "market_news": market_news,
        }
        
        # Validate entire snapshot
        payload, validation_errors = validate_snapshot_data(payload)
        if validation_errors:
            logger.warning(f"Snapshot validation issues: {validation_errors}")
        
        # Update cache
        _snapshot_cache["data"] = payload
        _snapshot_cache["timestamp"] = datetime.now()
        logger.info("Snapshot generated and cached")
        
        return payload
    except Exception as e:
        logger.error(f"Failed to generate snapshot: {e}")
        # Return basic snapshot without news on error
        return {
            "snapshot_date": date.today().isoformat(),
            "picks": [],
            "gainers": [],
            "losers": [],
            "metrics": {"universe_count": 0, "avg_return_pct": 0},
            "top_news": {},
            "market_news": [],
        }
    finally:
        await db.close()


async def get_latest_snapshot() -> dict | None:
    """
    Get latest snapshot from cache if available and fresh.
    Otherwise generate new snapshot.
    
    Cache strategy:
    - Return cached data if < 5 minutes old
    - Generate new snapshot if cache is stale
    - Background refresh (don't block user)
    """
    now = datetime.now()
    cache_duration = timedelta(minutes=_snapshot_cache["cache_duration_minutes"])
    
    # Check if cache is valid
    if (
        _snapshot_cache["data"] is not None
        and _snapshot_cache["timestamp"] is not None
        and (now - _snapshot_cache["timestamp"]) < cache_duration
    ):
        logger.info("Returning cached snapshot")
        return _snapshot_cache["data"]
    
    # Cache is stale or empty - generate new snapshot
    logger.info("Cache expired or empty, generating new snapshot")
    return await generate_daily_snapshot()


async def refresh_snapshot_cache():
    """
    Background task to refresh snapshot cache.
    Call this periodically (e.g., every 5 minutes) to keep cache fresh.
    """
    logger.info("Background snapshot refresh started")
    await generate_daily_snapshot()
    logger.info("Background snapshot refresh completed")


