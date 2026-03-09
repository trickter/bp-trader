from __future__ import annotations

from fastapi import APIRouter, Depends

from ....schemas import RiskControls
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
