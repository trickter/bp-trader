from __future__ import annotations

from fastapi import APIRouter, Depends

from ...auth import require_admin_api_token
from .routers import backtests, markets, operations, profile, strategies


api_router = APIRouter(prefix="/api", dependencies=[Depends(require_admin_api_token)])
api_router.include_router(profile.router)
api_router.include_router(strategies.router)
api_router.include_router(backtests.router)
api_router.include_router(markets.router)
api_router.include_router(operations.router)
