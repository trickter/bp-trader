from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ....schemas import PriceSource
from ..dependencies import get_services
from ....infrastructure.bootstrap import ServiceContainer


router = APIRouter(prefix="/markets")


@router.get("/pulse")
async def get_market_pulse(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.default_market_pulse()


@router.get("/pulse/{symbol}")
async def get_market_pulse_for_symbol(symbol: str, services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.market_pulse(symbol)


@router.get("/symbols")
def get_market_symbols(services: ServiceContainer = Depends(get_services)):
    return services.operator_queries.market_symbols()


@router.get("/{symbol}/klines")
async def get_klines(
    symbol: str,
    interval: str = Query(...),
    start_time: int = Query(..., description="UTC seconds"),
    end_time: int = Query(..., description="UTC seconds"),
    price_source: PriceSource = Query(...),
    services: ServiceContainer = Depends(get_services),
):
    return await services.operator_queries.klines(
        symbol=symbol,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        price_source=price_source,
    )
