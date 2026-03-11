from __future__ import annotations

from fastapi import APIRouter, Depends

from ....schemas import ExecutionRuntimeCommand, LiveStrategyEnableRequest, RiskControls
from ..dependencies import get_services
from ....infrastructure.bootstrap import ServiceContainer


router = APIRouter()


@router.get("/alerts")
def get_alerts(services: ServiceContainer = Depends(get_services)):
    return services.operator_queries.alerts(services.alerts)


@router.get("/risk-controls")
def get_risk_controls(services: ServiceContainer = Depends(get_services)):
    return services.operator_queries.risk_controls()


@router.put("/risk-controls")
def update_risk_controls(payload: RiskControls, services: ServiceContainer = Depends(get_services)):
    return services.operator_queries.update_risk_controls(payload)


@router.get("/settings/accounts")
@router.get("/settings/exchange-accounts")
async def get_exchange_accounts(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.exchange_accounts()


@router.get("/agent/capabilities")
async def get_agent_capabilities(services: ServiceContainer = Depends(get_services)):
    return [item.model_dump(by_alias=True) for item in services.operator_queries.capabilities()]


@router.get("/agent/context")
async def get_agent_context(services: ServiceContainer = Depends(get_services)):
    return await services.operator_queries.agent_context()


@router.get("/execution/live-strategies")
def get_live_strategies(services: ServiceContainer = Depends(get_services)):
    return [item.model_dump(by_alias=True) for item in services.execution_app.list_live_strategies()]


@router.post("/execution/live-strategies/{strategy_id}/enable")
def enable_live_strategy(
    strategy_id: str,
    payload: LiveStrategyEnableRequest,
    services: ServiceContainer = Depends(get_services),
):
    return services.execution_app.enable_live_strategy(strategy_id, payload).model_dump(by_alias=True)


@router.post("/execution/live-strategies/{strategy_id}/disable")
def disable_live_strategy(strategy_id: str, services: ServiceContainer = Depends(get_services)):
    return services.execution_app.disable_live_strategy(strategy_id).model_dump(by_alias=True)


@router.post("/execution/live-strategies/{strategy_id}/flatten")
async def flatten_live_strategy(
    strategy_id: str,
    payload: ExecutionRuntimeCommand,
    services: ServiceContainer = Depends(get_services),
):
    return (await services.execution_app.flatten_live_strategy(strategy_id, payload)).model_dump(by_alias=True)


@router.post("/execution/live-strategies/{strategy_id}/disable-and-flatten")
async def disable_and_flatten_live_strategy(
    strategy_id: str,
    payload: ExecutionRuntimeCommand,
    services: ServiceContainer = Depends(get_services),
):
    return (await services.execution_app.disable_and_flatten_live_strategy(strategy_id, payload)).model_dump(by_alias=True)


@router.get("/execution/runtime")
def get_execution_runtime(services: ServiceContainer = Depends(get_services)):
    return services.execution_app.runtime_status().model_dump(by_alias=True)


@router.post("/execution/runtime/start")
async def start_execution_runtime(
    payload: ExecutionRuntimeCommand,
    services: ServiceContainer = Depends(get_services),
):
    return (await services.execution_app.start_runtime(payload)).model_dump(by_alias=True)


@router.post("/execution/runtime/stop")
async def stop_execution_runtime(
    payload: ExecutionRuntimeCommand,
    services: ServiceContainer = Depends(get_services),
):
    return (await services.execution_app.stop_runtime(payload)).model_dump(by_alias=True)


@router.get("/execution/orders")
def get_execution_orders(services: ServiceContainer = Depends(get_services)):
    return [item.model_dump(by_alias=True) for item in services.execution_app.list_orders()]


@router.get("/execution/events")
def get_execution_events(services: ServiceContainer = Depends(get_services)):
    return [item.model_dump(by_alias=True) for item in services.execution_app.list_events()]
