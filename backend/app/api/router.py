from fastapi import APIRouter

from app.api.v1.endpoints import analysis, health, watchlist

api_router = APIRouter()
api_router.include_router(health.router, prefix="/v1", tags=["health"])
api_router.include_router(analysis.router, prefix="/v1", tags=["analysis"])
api_router.include_router(watchlist.router, prefix="/v1", tags=["watchlist"])
