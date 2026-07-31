from __future__ import annotations

from fastapi import APIRouter, Query
from loguru import logger

from app.services.snapshot_service import generate_daily_snapshot, get_latest_snapshot
from app.services.news_cache_service import get_cache_manager

router = APIRouter()


@router.get("/market/daily-snapshot")
async def market_snapshot() -> dict:
    snap = await get_latest_snapshot()
    if snap:
        return snap
    return await generate_daily_snapshot()


@router.get("/market/stocks")
async def get_stocks(
    category: str = Query("gainers", description="Category: picks, gainers, or losers"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(10, ge=1, le=10, description="Items per page (max 10)"),
) -> dict:
    """Get paginated stock data by category"""
    snap = await get_latest_snapshot()
    if not snap:
        snap = await generate_daily_snapshot()
    
    # Get the appropriate list
    stocks_list = snap.get(category, [])
    
    # Apply pagination
    paginated = stocks_list[offset : offset + limit]
    
    return {
        "category": category,
        "offset": offset,
        "limit": limit,
        "total": len(stocks_list),
        "items": paginated,
    }


@router.get("/stocks/{ticker}/news")
async def get_ticker_news(ticker: str) -> dict:
    """
    Get news for a specific ticker.
    
    Returns news from the news aggregator service.
    """
    try:
        from app.services.news_aggregator_service import get_news_aggregator
        
        news_agg = get_news_aggregator()
        articles = await news_agg.get_ticker_news(ticker, limit=20)
        
        return {
            "ticker": ticker,
            "items": articles,
        }
    except Exception as e:
        logger.error(f"Failed to get news for {ticker}: {e}")
        return {
            "ticker": ticker,
            "items": [],
            "error": str(e),
        }


@router.get("/market/news")
async def get_news(
    category: str = Query("general", description="News category: general, finance, it, healthcare, energy, real_estate"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
) -> dict:
    """
    Get paginated market news by category from Redis cache.
    
    This endpoint reads from pre-cached news that is refreshed by background workers:
    - General news: refreshed every 10 minutes
    - Category news: refreshed every 15 minutes
    
    No external API calls are made during request handling.
    """
    try:
        cache_manager = get_cache_manager()
        
        # Get cached news for the category
        result = await cache_manager.get_cached_news(category, page)
        
        if not result.get("cached"):
            logger.warning(f"No cached news available for {category}, page {page}")
        
        return result
    except Exception as e:
        logger.error(f"Failed to get news for {category}: {e}")
        return {
            "category": category,
            "page": page,
            "per_page": 10,
            "total": 0,
            "total_pages": 0,
            "items": [],
            "cached": False,
            "error": str(e),
        }


@router.get("/market/news/stats")
async def get_news_stats() -> dict:
    """Get cache statistics for all news categories"""
    try:
        cache_manager = get_cache_manager()
        stats = await cache_manager.get_cache_stats()
        return {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "categories": stats,
        }
    except Exception as e:
        logger.error(f"Failed to get news stats: {e}")
        return {
            "error": str(e),
            "categories": {},
        }


