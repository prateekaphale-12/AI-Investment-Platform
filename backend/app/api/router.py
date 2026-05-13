from fastapi import APIRouter

from app.api.v1.endpoints import analysis, auth, health, watchlist, market, llm

api_router = APIRouter()
api_router.include_router(health.router, prefix="/v1", tags=["health"])
api_router.include_router(auth.router, prefix="/v1", tags=["auth"])
api_router.include_router(analysis.router, prefix="/v1", tags=["analysis"])
api_router.include_router(watchlist.router, prefix="/v1", tags=["watchlist"])
api_router.include_router(market.router, prefix="/v1", tags=["market"])
api_router.include_router(llm.router, prefix="/v1/llm", tags=["llm"])
