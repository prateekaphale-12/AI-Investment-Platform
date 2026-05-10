from contextlib import asynccontextmanager
import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.db.init_db import init_db
from app.services.snapshot_service import generate_daily_snapshot
from app.utils.logger import setup_logging

setup_logging()

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    is_test = bool(os.getenv("PYTEST_CURRENT_TEST"))
    if not is_test:
        if not scheduler.running:
            scheduler.add_job(generate_daily_snapshot, "interval", hours=24, id="daily-snapshot", replace_existing=True)
            scheduler.start()
        await generate_daily_snapshot()
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
