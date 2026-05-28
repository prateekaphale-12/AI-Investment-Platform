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
            logger.info("APScheduler started with news ingestion tasks")
        
        # Warm up cache on startup (non-blocking)
        asyncio.create_task(_warm_daily_snapshot_background())
        
        # Warm up news cache on startup (non-blocking)
        async def _warm_news_cache():
            try:
                worker = get_ingestion_worker()
                # Ingest general news immediately
                await worker.run_ingestion_cycle("general")
                logger.info("News cache warmed up on startup")
            except Exception as e:
                logger.warning(f"News cache warmup failed (will retry on schedule): {e}")
        
        asyncio.create_task(_warm_news_cache())
        
        # Start real-time services (non-blocking)
        try:
            from app.services.realtime.launcher import start_realtime_services
            asyncio.create_task(start_realtime_services())
            logger.info("Real-time services started")
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
