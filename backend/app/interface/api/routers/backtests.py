from __future__ import annotations

from fastapi import APIRouter, Depends

from ....schemas import BacktestRequest
from ..dependencies import get_services
from ....infrastructure.bootstrap import ServiceContainer


router = APIRouter()


@router.post("/strategies/templates/{template_id}/backtests")
async def create_template_backtest(
    template_id: str,
    request: BacktestRequest,
    services: ServiceContainer = Depends(get_services),
):
    result = await services.backtest_app.create_run(strategy_id=template_id, strategy_kind="template", request=request)
    return result.model_dump(by_alias=True)


@router.post("/strategies/scripts/{strategy_id}/backtests")
async def create_script_backtest(
    strategy_id: str,
    request: BacktestRequest,
    services: ServiceContainer = Depends(get_services),
):
    result = await services.backtest_app.create_run(strategy_id=strategy_id, strategy_kind="script", request=request)
    return result.model_dump(by_alias=True)


@router.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str, services: ServiceContainer = Depends(get_services)):
    return services.backtest_app.get_run(backtest_id).model_dump(by_alias=True)
