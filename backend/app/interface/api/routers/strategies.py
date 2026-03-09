from __future__ import annotations

from fastapi import APIRouter, Depends, status

from ....schemas import StrategyUpsertRequest
from ..dependencies import get_services
from ....infrastructure.bootstrap import ServiceContainer


router = APIRouter(prefix="/strategies")


@router.get("")
def get_strategies(services: ServiceContainer = Depends(get_services)):
    return [item.model_dump(by_alias=True) for item in services.strategy_app.list_strategies()]


@router.get("/{strategy_id}")
def get_strategy(strategy_id: str, services: ServiceContainer = Depends(get_services)):
    return services.strategy_app.get_strategy(strategy_id).model_dump(by_alias=True)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_strategy(payload: StrategyUpsertRequest, services: ServiceContainer = Depends(get_services)):
    return services.strategy_app.create_strategy(payload).model_dump(by_alias=True)


@router.put("/{strategy_id}")
def update_strategy(
    strategy_id: str,
    payload: StrategyUpsertRequest,
    services: ServiceContainer = Depends(get_services),
):
    return services.strategy_app.update_strategy(strategy_id, payload).model_dump(by_alias=True)
