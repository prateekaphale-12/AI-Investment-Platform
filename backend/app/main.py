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


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    is_test = bool(os.getenv("PYTEST_CURRENT_TEST")) or os.getenv("PYTEST_RUNNING") == "1"
    if not is_test:
        if not scheduler.running:
            scheduler.add_job(generate_daily_snapshot, "interval", hours=24, id="daily-snapshot", replace_existing=True)
            scheduler.start()
        asyncio.create_task(_warm_daily_snapshot_background())
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


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
