from contextlib import asynccontextmanager
import asyncio
import os
import warnings

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from langchain_core._api.deprecation import LangChainPendingDeprecationWarning

    warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
except ImportError:  # pragma: no cover
    pass

from app.api.router import api_router
from app.config import settings
from app.db.init_db import init_db
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.snapshot_service import generate_daily_snapshot
from app.services.news_ingestion_service import get_ingestion_worker
from app.utils.logger import setup_logging
from loguru import logger

setup_logging()

scheduler = AsyncIOScheduler()


async def _warm_daily_snapshot_background() -> None:
    """yfinance-heavy; must not block Uvicorn 'Application startup complete'."""
    try:
        await generate_daily_snapshot()
    except Exception as e:
        logger.warning("Daily snapshot warmup failed (will retry on schedule): {}", e)


async def _ingest_news_general() -> None:
    """Background task: Ingest general news (10 min interval)"""
    try:
        worker = get_ingestion_worker()
        result = await worker.run_ingestion_cycle("general")
        logger.info(f"General news ingestion completed: {result}")
    except Exception as e:
        logger.error(f"General news ingestion failed: {e}")


async def _ingest_news_category(category: str) -> None:
    """Background task: Ingest category-specific news (15 min interval)"""
    try:
        worker = get_ingestion_worker()
        result = await worker.run_ingestion_cycle(category)
        logger.info(f"{category} news ingestion completed: {result}")
    except Exception as e:
        logger.error(f"{category} news ingestion failed: {e}")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    is_test = bool(os.getenv("PYTEST_CURRENT_TEST")) or os.getenv("PYTEST_RUNNING") == "1"
    if not is_test:
        if not scheduler.running:
            # Warm up news cache FIRST (before scheduler starts)
            logger.info("Starting news cache warmup...")
            try:
                worker = get_ingestion_worker()
                categories = ["general", "finance", "it", "healthcare", "energy", "real_estate"]
                for category in categories:
                    try:
                        logger.info(f"Warming up {category} news...")
                        result = await worker.run_ingestion_cycle(category)
                        logger.info(f"✓ Warmed up {category}: {result}")
                    except Exception as e:
                        logger.error(f"✗ Failed to warm up {category}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"News cache warmup failed: {e}", exc_info=True)
            
            logger.info("News cache warmup completed, starting scheduler...")
            
            # Refresh snapshot every 30 minutes
            # Stock data (yfinance): FREE, no rate limits
            # News data (Alpha Vantage + NewsAPI): Limited, but 30-min refresh is safe
            # 30-minute refresh = 1,920 yfinance calls/day (very respectful)
            scheduler.add_job(
                generate_daily_snapshot,
                "interval",
                minutes=30,
                id="snapshot-refresh",
                replace_existing=True,
            )
            
            # News ingestion tasks
            # General news: every 10 minutes (homepage feed)
            scheduler.add_job(
                _ingest_news_general,
                "interval",
                minutes=10,
                id="news-general-ingest",
                replace_existing=True,
            )
            
            # Category-specific news: every 15 minutes
            categories = ["finance", "it", "healthcare", "energy", "real_estate"]
            for category in categories:
                scheduler.add_job(
                    _ingest_news_category,
                    "interval",
                    minutes=15,
                    args=[category],
                    id=f"news-{category}-ingest",
                    replace_existing=True,
                )
            
            scheduler.start()
            logger.info("✓ APScheduler started with news ingestion tasks")
        
        # Warm up daily snapshot in background
        asyncio.create_task(_warm_daily_snapshot_background())
        
        # Start real-time services (non-blocking)
        try:
            from app.services.realtime.launcher import start_realtime_services
            asyncio.create_task(start_realtime_services())
            logger.info("✓ Real-time services started")
        except Exception as e:
            logger.warning(f"Real-time services not started: {e}")
    
    yield
    
    if scheduler.running:
        scheduler.shutdown(wait=False)
    
    # Stop real-time services
    try:
        from app.services.realtime.launcher import stop_realtime_services
        await stop_realtime_services()
    except:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Add rate limiting middleware (must be added before CORS)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=5,  # 5 requests
    window_seconds=60,  # per minute
    paths=["/api/v1/auth/login", "/api/v1/auth/register"],  # Only rate limit auth endpoints
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "AI Investment Research API", "docs": "/docs"}
