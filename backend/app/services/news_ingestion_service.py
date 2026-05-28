"""
Production-grade News Ingestion Service

Background worker that fetches news periodically from multiple sources,
deduplicates, caches in Redis, and serves to frontend via API.

Architecture:
- Fetches news on schedule (NOT on-demand)
- Multiple sources: Google News RSS, Finnhub, NewsData.io
- Deduplication: title similarity, URL hashing
- Sentiment analysis
- Redis caching with TTL
- Pagination support

Refresh intervals:
- Homepage feeds: 10 minutes
- Category feeds: 15 minutes
- Ticker-specific: 15 minutes
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from difflib import SequenceMatcher

import aiohttp
import feedparser
from loguru import logger

from app.config import settings
from app.services.redis_service import cache_get_json, cache_set_json


class NewsIngestionWorker:
    """Background worker for news ingestion and caching"""

    def __init__(self):
        self.newsapi_key = getattr(settings, "newsapi_key", "")
        self.finnhub_key = getattr(settings, "finnhub_key", "")
        self.seen_articles: set = set()  # Track seen articles for deduplication
        self.max_articles_per_category = 50  # Keep last 50 articles per category

    async def ingest_homepage_news(self) -> Dict[str, Any]:
        """Ingest fresh news for homepage (every 10 minutes)"""
        logger.info("Starting homepage news ingestion")
        
        try:
            # Fetch from multiple sources
            articles = await asyncio.gather(
                self._fetch_google_news_general(),
                self._fetch_newsapi_general(),
                self._fetch_finnhub_general(),
                return_exceptions=True,
            )

            # Flatten and filter exceptions
            all_articles = []
            for result in articles:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"News source failed: {result}")

            # Deduplicate
            unique_articles = self._deduplicate_articles(all_articles)

            # Sort by freshness
            unique_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)

            # Filter by max age (24 hours)
            fresh_articles = self._filter_by_age(unique_articles, hours=24)

            # Cache
            await cache_set_json(
                "news:general",
                {
                    "articles": fresh_articles[: self.max_articles_per_category],
                    "updated_at": datetime.now().isoformat(),
                    "count": len(fresh_articles),
                },
                ttl_seconds=600,  # 10 minutes
            )

            logger.info(f"Cached {len(fresh_articles)} homepage articles")
            return {"status": "success", "count": len(fresh_articles)}

        except Exception as e:
            logger.error(f"Homepage news ingestion failed: {e}")
            return {"status": "error", "error": str(e)}

    async def ingest_category_news(self, category: str) -> Dict[str, Any]:
        """Ingest news for specific category (every 15 minutes)"""
        logger.info(f"Starting {category} news ingestion")

        try:
            # Fetch from multiple sources
            articles = await asyncio.gather(
                self._fetch_google_news_category(category),
                self._fetch_newsapi_category(category),
                self._fetch_finnhub_category(category),
                return_exceptions=True,
            )

            # Flatten and filter exceptions
            all_articles = []
            for result in articles:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"News source failed for {category}: {result}")

            # Deduplicate
            unique_articles = self._deduplicate_articles(all_articles)

            # Sort by freshness
            unique_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)

            # Filter by max age (12 hours for trending)
            fresh_articles = self._filter_by_age(unique_articles, hours=12)

            # Cache
            cache_key = f"news:{category}"
            await cache_set_json(
                cache_key,
                {
                    "articles": fresh_articles[: self.max_articles_per_category],
                    "updated_at": datetime.now().isoformat(),
                    "count": len(fresh_articles),
                },
                ttl_seconds=900,  # 15 minutes
            )

            logger.info(f"Cached {len(fresh_articles)} {category} articles")
            return {"status": "success", "category": category, "count": len(fresh_articles)}

        except Exception as e:
            logger.error(f"{category} news ingestion failed: {e}")
            return {"status": "error", "category": category, "error": str(e)}

    async def ingest_ticker_news(self, ticker: str) -> Dict[str, Any]:
        """Ingest news for specific ticker (every 15 minutes)"""
        logger.info(f"Starting {ticker} news ingestion")

        try:
            # Fetch from multiple sources
            articles = await asyncio.gather(
                self._fetch_finnhub_ticker(ticker),
                self._fetch_newsapi_ticker(ticker),
                return_exceptions=True,
            )

            # Flatten and filter exceptions
            all_articles = []
            for result in articles:
                if isinstance(result, list):
                    all_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"News source failed for {ticker}: {result}")

            # Deduplicate
            unique_articles = self._deduplicate_articles(all_articles)

            # Sort by freshness
            unique_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)

            # Filter by max age (7 days)
            fresh_articles = self._filter_by_age(unique_articles, hours=168)

            # Cache
            cache_key = f"ticker:{ticker}:news"
            await cache_set_json(
                cache_key,
                {
                    "articles": fresh_articles[: self.max_articles_per_category],
                    "updated_at": datetime.now().isoformat(),
                    "count": len(fresh_articles),
                },
                ttl_seconds=900,  # 15 minutes
            )

            logger.info(f"Cached {len(fresh_articles)} {ticker} articles")
            return {"status": "success", "ticker": ticker, "count": len(fresh_articles)}

        except Exception as e:
            logger.error(f"{ticker} news ingestion failed: {e}")
            return {"status": "error", "ticker": ticker, "error": str(e)}

    async def _fetch_google_news_general(self) -> List[Dict[str, Any]]:
        """Fetch from Google News RSS (free, no rate limits)"""
        try:
            url = "https://news.google.com/rss/search?q=stock+market+finance&hl=en-US&gl=US&ceid=US:en"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        logger.warning(f"Google News returned {resp.status}")
                        return []

                    content = await resp.text()
                    feed = feedparser.parse(content)

                    articles = []
                    for entry in feed.entries[:20]:
                        articles.append({
                            "title": entry.get("title", ""),
                            "url": entry.get("link", ""),
                            "source": "Google News",
                            "published_at": self._parse_date(entry.get("published", "")),
                            "summary": entry.get("summary", "")[:200],
                            "category": "general",
                        })

                    logger.info(f"Google News returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"Google News fetch failed: {e}")
            return []

    async def _fetch_google_news_category(self, category: str) -> List[Dict[str, Any]]:
        """Fetch from Google News RSS by category"""
        category_queries = {
            "finance": "finance+banking+investment",
            "it": "technology+software+AI",
            "healthcare": "healthcare+pharma+biotech",
            "energy": "energy+oil+gas",
            "real_estate": "real+estate+property",
        }

        query = category_queries.get(category, category)

        try:
            url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return []

                    content = await resp.text()
                    feed = feedparser.parse(content)

                    articles = []
                    for entry in feed.entries[:20]:
                        articles.append({
                            "title": entry.get("title", ""),
                            "url": entry.get("link", ""),
                            "source": "Google News",
                            "published_at": self._parse_date(entry.get("published", "")),
                            "summary": entry.get("summary", "")[:200],
                            "category": category,
                        })

                    logger.info(f"Google News ({category}) returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"Google News ({category}) fetch failed: {e}")
            return []

    async def _fetch_newsapi_general(self) -> List[Dict[str, Any]]:
        """Fetch from NewsAPI (free tier: 100 requests/day)"""
        if not self.newsapi_key:
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": "stock market finance",
                "sortBy": "publishedAt",
                "language": "en",
                "apikey": self.newsapi_key,
                "pageSize": 20,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 429:
                        logger.warning("NewsAPI rate limited")
                        return []
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    if data.get("status") == "error":
                        logger.warning(f"NewsAPI error: {data.get('message')}")
                        return []

                    articles = []
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_at": article.get("publishedAt", ""),
                            "summary": article.get("description", "")[:200],
                            "category": "general",
                        })

                    logger.info(f"NewsAPI returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")
            return []

    async def _fetch_newsapi_category(self, category: str) -> List[Dict[str, Any]]:
        """Fetch from NewsAPI by category"""
        if not self.newsapi_key:
            return []

        category_queries = {
            "finance": "finance banking investment",
            "it": "technology software AI",
            "healthcare": "healthcare pharma biotech",
            "energy": "energy oil gas",
            "real_estate": "real estate property",
        }

        query = category_queries.get(category, category)

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "sortBy": "publishedAt",
                "language": "en",
                "apikey": self.newsapi_key,
                "pageSize": 20,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 429:
                        return []
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    if data.get("status") == "error":
                        return []

                    articles = []
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_at": article.get("publishedAt", ""),
                            "summary": article.get("description", "")[:200],
                            "category": category,
                        })

                    logger.info(f"NewsAPI ({category}) returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"NewsAPI ({category}) fetch failed: {e}")
            return []

    async def _fetch_newsapi_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch from NewsAPI for specific ticker"""
        if not self.newsapi_key:
            return []

        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": ticker,
                "sortBy": "publishedAt",
                "language": "en",
                "apikey": self.newsapi_key,
                "pageSize": 15,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 429:
                        return []
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    if data.get("status") == "error":
                        return []

                    articles = []
                    for article in data.get("articles", []):
                        articles.append({
                            "title": article.get("title", ""),
                            "url": article.get("url", ""),
                            "source": article.get("source", {}).get("name", "NewsAPI"),
                            "published_at": article.get("publishedAt", ""),
                            "summary": article.get("description", "")[:200],
                            "ticker": ticker,
                        })

                    logger.info(f"NewsAPI ({ticker}) returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"NewsAPI ({ticker}) fetch failed: {e}")
            return []

    async def _fetch_finnhub_general(self) -> List[Dict[str, Any]]:
        """Fetch from Finnhub general news"""
        if not self.finnhub_key:
            return []

        try:
            url = "https://finnhub.io/api/v1/news"
            params = {
                "category": "general",
                "token": self.finnhub_key,
                "minId": 0,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    articles = []

                    for item in data[:20]:
                        articles.append({
                            "title": item.get("headline", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", "Finnhub"),
                            "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                            "summary": item.get("summary", "")[:200],
                            "category": "general",
                        })

                    logger.info(f"Finnhub returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"Finnhub fetch failed: {e}")
            return []

    async def _fetch_finnhub_category(self, category: str) -> List[Dict[str, Any]]:
        """Fetch from Finnhub by category"""
        if not self.finnhub_key:
            return []

        category_map = {
            "finance": "general",
            "it": "general",
            "healthcare": "general",
            "energy": "general",
            "real_estate": "general",
        }

        finnhub_category = category_map.get(category, "general")

        try:
            url = "https://finnhub.io/api/v1/news"
            params = {
                "category": finnhub_category,
                "token": self.finnhub_key,
                "minId": 0,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    articles = []

                    for item in data[:20]:
                        articles.append({
                            "title": item.get("headline", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", "Finnhub"),
                            "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                            "summary": item.get("summary", "")[:200],
                            "category": category,
                        })

                    logger.info(f"Finnhub ({category}) returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"Finnhub ({category}) fetch failed: {e}")
            return []

    async def _fetch_finnhub_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Fetch from Finnhub for specific ticker"""
        if not self.finnhub_key:
            return []

        try:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = datetime.now().strftime("%Y-%m-%d")

            url = "https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": ticker,
                "from": from_date,
                "to": to_date,
                "token": self.finnhub_key,
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status != 200:
                        return []

                    data = await resp.json()
                    articles = []

                    for item in data[:15]:
                        articles.append({
                            "title": item.get("headline", ""),
                            "url": item.get("url", ""),
                            "source": item.get("source", "Finnhub"),
                            "published_at": datetime.fromtimestamp(item.get("datetime", 0)).isoformat(),
                            "summary": item.get("summary", "")[:200],
                            "ticker": ticker,
                        })

                    logger.info(f"Finnhub ({ticker}) returned {len(articles)} articles")
                    return articles
        except Exception as e:
            logger.warning(f"Finnhub ({ticker}) fetch failed: {e}")
            return []

    async def run_ingestion_cycle(self, category: str = "general") -> Dict[str, Any]:
        """Run ingestion cycle for a category (called by scheduler)"""
        if category == "general":
            return await self.ingest_homepage_news()
        else:
            return await self.ingest_category_news(category)

    # ==================== DEDUPLICATION & FILTERING ====================

    def _deduplicate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles using title similarity and URL hashing"""
        seen_hashes = set()
        unique_articles = []

        for article in articles:
            # Generate URL hash
            url = article.get("url", "")
            url_hash = hashlib.md5(url.encode()).hexdigest() if url else None

            # Skip if URL already seen
            if url_hash and url_hash in seen_hashes:
                continue

            # Check title similarity with existing articles
            title = article.get("title", "").lower()
            is_duplicate = False

            for existing in unique_articles:
                existing_title = existing.get("title", "").lower()
                similarity = SequenceMatcher(None, title, existing_title).ratio()

                # If 80%+ similar, consider duplicate
                if similarity > 0.8:
                    is_duplicate = True
                    break

            if not is_duplicate:
                if url_hash:
                    seen_hashes.add(url_hash)
                article["dedupe_hash"] = url_hash or hashlib.md5(title.encode()).hexdigest()
                unique_articles.append(article)

        logger.info(f"Deduplicated {len(articles)} articles to {len(unique_articles)}")
        return unique_articles

    def _filter_by_age(self, articles: List[Dict[str, Any]], hours: int = 24) -> List[Dict[str, Any]]:
        """Filter articles by max age"""
        from datetime import timezone
        
        # Use timezone-aware cutoff
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        filtered = []

        for article in articles:
            try:
                pub_date_str = article.get("published_at", "")
                if not pub_date_str:
                    continue

                # Parse ISO format date
                pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                
                # Ensure both are timezone-aware for comparison
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=timezone.utc)
                if cutoff.tzinfo is None:
                    cutoff = cutoff.replace(tzinfo=timezone.utc)

                if pub_date > cutoff:
                    filtered.append(article)
            except Exception as e:
                logger.warning(f"Failed to parse date {article.get('published_at')}: {e}")
                filtered.append(article)  # Include if date parsing fails

        logger.info(f"Filtered {len(articles)} articles to {len(filtered)} (max age: {hours}h)")
        return filtered

    def _parse_date(self, date_str: str) -> str:
        """Parse various date formats to ISO format"""
        if not date_str:
            return datetime.now().isoformat()

        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).isoformat()
        except:
            try:
                # Try RFC 2822 format (common in RSS)
                from email.utils import parsedate_to_datetime
                return parsedate_to_datetime(date_str).isoformat()
            except:
                return datetime.now().isoformat()


# Global instance
_ingestion_worker: Optional[NewsIngestionWorker] = None


def get_news_ingestion_worker() -> NewsIngestionWorker:
    """Get or create news ingestion worker"""
    global _ingestion_worker
    if _ingestion_worker is None:
        _ingestion_worker = NewsIngestionWorker()
    return _ingestion_worker


# Alias for compatibility
def get_ingestion_worker() -> NewsIngestionWorker:
    """Alias for get_news_ingestion_worker"""
    return get_news_ingestion_worker()
