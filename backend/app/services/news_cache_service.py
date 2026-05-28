"""
News Cache Service

Manages Redis caching for news articles with pagination support.
Provides efficient retrieval of cached news without external API calls.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from loguru import logger

from app.services.redis_service import cache_get_json, cache_set_json


class NewsCacheManager:
    """Manages cached news with pagination"""

    def __init__(self):
        self.articles_per_page = 10
        self.cache_ttl = 900  # 15 minutes

    async def get_cached_news(
        self,
        category: str = "general",
        page: int = 1,
    ) -> Dict[str, Any]:
        """Get paginated cached news for category"""
        try:
            cache_key = f"news:{category}"
            cached_data = await cache_get_json(cache_key)

            if not cached_data:
                logger.warning(f"No cached news for category: {category}")
                return {
                    "category": category,
                    "page": page,
                    "per_page": self.articles_per_page,
                    "total": 0,
                    "total_pages": 0,
                    "items": [],
                    "cached": False,
                }

            articles = cached_data.get("articles", [])
            total = len(articles)
            total_pages = (total + self.articles_per_page - 1) // self.articles_per_page

            # Paginate
            start_idx = (page - 1) * self.articles_per_page
            end_idx = start_idx + self.articles_per_page
            paginated = articles[start_idx:end_idx]

            return {
                "category": category,
                "page": page,
                "per_page": self.articles_per_page,
                "total": total,
                "total_pages": total_pages,
                "items": paginated,
                "cached": True,
                "updated_at": cached_data.get("updated_at"),
            }

        except Exception as e:
            logger.error(f"Failed to get cached news for {category}: {e}")
            return {
                "category": category,
                "page": page,
                "per_page": self.articles_per_page,
                "total": 0,
                "total_pages": 0,
                "items": [],
                "cached": False,
                "error": str(e),
            }

    async def get_ticker_news(
        self,
        ticker: str,
        page: int = 1,
    ) -> Dict[str, Any]:
        """Get paginated cached news for ticker"""
        try:
            cache_key = f"ticker:{ticker}:news"
            cached_data = await cache_get_json(cache_key)

            if not cached_data:
                logger.warning(f"No cached news for ticker: {ticker}")
                return {
                    "ticker": ticker,
                    "page": page,
                    "per_page": self.articles_per_page,
                    "total": 0,
                    "total_pages": 0,
                    "items": [],
                    "cached": False,
                }

            articles = cached_data.get("articles", [])
            total = len(articles)
            total_pages = (total + self.articles_per_page - 1) // self.articles_per_page

            # Paginate
            start_idx = (page - 1) * self.articles_per_page
            end_idx = start_idx + self.articles_per_page
            paginated = articles[start_idx:end_idx]

            return {
                "ticker": ticker,
                "page": page,
                "per_page": self.articles_per_page,
                "total": total,
                "total_pages": total_pages,
                "items": paginated,
                "cached": True,
                "updated_at": cached_data.get("updated_at"),
            }

        except Exception as e:
            logger.error(f"Failed to get cached news for {ticker}: {e}")
            return {
                "ticker": ticker,
                "page": page,
                "per_page": self.articles_per_page,
                "total": 0,
                "total_pages": 0,
                "items": [],
                "cached": False,
                "error": str(e),
            }

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for all categories"""
        categories = ["general", "finance", "it", "healthcare", "energy", "real_estate"]
        stats = {}

        for category in categories:
            try:
                cache_key = f"news:{category}"
                cached_data = await cache_get_json(cache_key)
                
                if cached_data:
                    articles = cached_data.get("articles", [])
                    stats[category] = {
                        "count": len(articles),
                        "updated_at": cached_data.get("updated_at"),
                        "cached": True,
                    }
                else:
                    stats[category] = {
                        "count": 0,
                        "cached": False,
                    }
            except Exception as e:
                logger.warning(f"Failed to get stats for {category}: {e}")
                stats[category] = {
                    "count": 0,
                    "cached": False,
                    "error": str(e),
                }

        return stats

    async def get_all_categories(self) -> Dict[str, Any]:
        """Get news for all categories"""
        categories = ["general", "finance", "it", "healthcare", "energy", "real_estate"]
        results = {}

        for category in categories:
            data = await self.get_cached_news(category, page=1)
            results[category] = data

        return results


# Global instance
_cache_manager: Optional[NewsCacheManager] = None


def get_cache_manager() -> NewsCacheManager:
    """Get or create news cache manager"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = NewsCacheManager()
    return _cache_manager
