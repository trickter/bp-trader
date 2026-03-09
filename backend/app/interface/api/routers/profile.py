from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_services
from ....infrastructure.bootstrap import ServiceContainer


router = APIRouter(prefix="/profile")


@router.get("/summary")
async def get_profile_summary(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.profile_summary()


@router.get("/assets")
async def get_profile_assets(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.profile_assets()


@router.get("/positions")
async def get_profile_positions(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.profile_positions()


@router.get("/account-events")
async def get_account_events(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.profile_account_events()
