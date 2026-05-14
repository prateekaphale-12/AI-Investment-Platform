"""
News aggregation service - pulls from multiple free sources
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from loguru import logger

from app.config import settings


class NewsAggregator:
    """Aggregate news from multiple free sources"""

    def __init__(self):
        self.alpha_vantage_key = getattr(settings, "alpha_vantage_key", "")
        self.newsapi_key = getattr(settings, "newsapi_key", "")

    async def get_ticker_news(self, ticker: str, limit: int = 5) -> list[dict[str, Any]]:
        """Get latest news for a ticker from multiple sources"""
        try:
            logger.info(f"Fetching news for {ticker} (Alpha Vantage key: {bool(self.alpha_vantage_key)}, NewsAPI key: {bool(self.newsapi_key)})")
            
            tasks = [
                self._get_alpha_vantage_news(ticker, limit),
                self._get_newsapi_news(ticker, limit),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_news = []
            for i, result in enumerate(results):
                if isinstance(result, list):
                    logger.info(f"Source {i} returned {len(result)} articles")
                    all_news.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"News source {i} failed: {result}")

            logger.info(f"Total articles before dedup: {len(all_news)}")
            
            # Deduplicate and sort by date
            seen = set()
            unique_news = []
            for article in all_news:
                key = (article.get("title", ""), article.get("source", ""))
                if key not in seen:
                    seen.add(key)
                    unique_news.append(article)

            # Sort by date descending
            unique_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
            logger.info(f"Returning {len(unique_news[:limit])} articles for {ticker}")
            return unique_news[:limit]
        except Exception as e:
            logger.error(f"Failed to get news for {ticker}: {e}")
            return []

    async def _get_alpha_vantage_news(self, ticker: str, limit: int) -> list[dict[str, Any]]:
        """Get news from Alpha Vantage (free tier)"""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage key not configured")
            return []

        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "apikey": self.alpha_vantage_key,
                "limit": limit,
            }

            logger.info(f"Calling Alpha Vantage for {ticker}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.info(f"Alpha Vantage response status: {resp.status}")
                    if resp.status != 200:
                        logger.warning(f"Alpha Vantage returned {resp.status}")
                        return []

                    data = await resp.json()
                    feed = data.get("feed", [])
                    logger.info(f"Alpha Vantage returned {len(feed)} articles for {ticker}")

                    news = []
                    for item in feed[:limit]:
                        news.append(
                            {
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "source": item.get("source", "Alpha Vantage"),
                                "published_at": item.get("time_published", ""),
                                "summary": item.get("summary", ""),
                                "sentiment": item.get("overall_sentiment_label", "NEUTRAL"),
                                "sentiment_score": float(item.get("overall_sentiment_score", 0)),
                            }
                        )
                    return news
        except Exception as e:
            logger.warning(f"Alpha Vantage news failed: {e}")
            return []

    async def _get_newsapi_news(self, ticker: str, limit: int) -> list[dict[str, Any]]:
        """Get news from NewsAPI (free tier: 100 requests/day)"""
        if not self.newsapi_key:
            logger.warning("NewsAPI key not configured")
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": ticker,
                "sortBy": "publishedAt",
                "language": "en",
                "apikey": self.newsapi_key,
                "pageSize": limit,
            }

            logger.info(f"Calling NewsAPI for {ticker}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.info(f"NewsAPI response status: {resp.status}")
                    if resp.status != 200:
                        logger.warning(f"NewsAPI returned {resp.status}")
                        return []

                    data = await resp.json()
                    articles = data.get("articles", [])
                    logger.info(f"NewsAPI returned {len(articles)} articles for {ticker}")

                    news = []
                    for article in articles[:limit]:
                        news.append(
                            {
                                "title": article.get("title", ""),
                                "url": article.get("url", ""),
                                "source": article.get("source", {}).get("name", "NewsAPI"),
                                "published_at": article.get("publishedAt", ""),
                                "summary": article.get("description", ""),
                                "image": article.get("urlToImage", ""),
                                "sentiment": "NEUTRAL",  # Would need separate sentiment analysis
                            }
                        )
                    return news
        except Exception as e:
            logger.warning(f"NewsAPI failed: {e}")
            return []

    async def get_market_news(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get general market news - filtered for stock/market relevance"""
        if not self.newsapi_key:
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "stock market stocks trading finance earnings investment portfolio",
                "sortBy": "publishedAt",
                "language": "en",
                "apikey": self.newsapi_key,
                "pageSize": limit * 2,  # Fetch more to filter
            }

            logger.info("Calling NewsAPI for market news")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.info(f"NewsAPI market news response status: {resp.status}")
                    if resp.status != 200:
                        logger.warning(f"NewsAPI returned {resp.status}")
                        return []

                    data = await resp.json()
                    articles = data.get("articles", [])
                    logger.info(f"NewsAPI returned {len(articles)} articles for market news")

                    # Filter for market/stock relevance
                    market_keywords = {
                        "stock", "market", "trading", "finance", "earnings", "investment",
                        "portfolio", "bull", "bear", "rally", "crash", "ipo", "sec",
                        "nasdaq", "dow", "s&p", "crypto", "bitcoin", "etf", "mutual fund",
                        "dividend", "analyst", "rating", "upgrade", "downgrade", "merger",
                        "acquisition", "ipo", "bankruptcy", "debt", "equity", "bond"
                    }
                    
                    filtered_news = []
                    for article in articles:
                        title_lower = (article.get("title", "") or "").lower()
                        summary_lower = (article.get("description", "") or "").lower()
                        source_lower = (article.get("source", {}).get("name", "") or "").lower()
                        
                        # Skip if source is known non-market source
                        if any(skip in source_lower for skip in ["game of thrones", "entertainment", "sports", "weather"]):
                            continue
                        
                        # Check if article contains market keywords
                        combined_text = f"{title_lower} {summary_lower}"
                        if any(keyword in combined_text for keyword in market_keywords):
                            filtered_news.append(
                                {
                                    "title": article.get("title", ""),
                                    "url": article.get("url", ""),
                                    "source": article.get("source", {}).get("name", "NewsAPI"),
                                    "published_at": article.get("publishedAt", ""),
                                    "summary": article.get("description", ""),
                                    "image": article.get("urlToImage", ""),
                                }
                            )
                        
                        if len(filtered_news) >= limit:
                            break
                    
                    logger.info(f"Filtered to {len(filtered_news)} market-relevant articles")
                    return filtered_news
        except Exception as e:
            logger.warning(f"Market news failed: {e}")
            return []


# Global instance
_aggregator = None


def get_news_aggregator() -> NewsAggregator:
    """Get or create news aggregator instance"""
    global _aggregator
    if _aggregator is None:
        _aggregator = NewsAggregator()
    return _aggregator
