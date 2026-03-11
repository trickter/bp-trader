from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI

from ..application.services.backtest_application_service import BacktestApplicationService
from ..application.services.live_execution_application_service import LiveExecutionApplicationService
from ..application.services.operator_query_service import OperatorQueryService
from ..application.services.strategy_application_service import StrategyApplicationService
from ..backpack import BackpackAuthConfig, BackpackClient
from .. import config as config_module
from ..mock_data import ALERTS, BACKTEST_RESULT, MARKET_SYMBOLS, RISK_CONTROLS, STRATEGIES, build_backtest_acceptance
from ..providers import BackpackProvider
from ..schemas import PriceSource
from .gateways.operator_gateway import OperatorGateway
from .gateways.execution_gateway import BackpackExecutionGateway
from .repositories.in_memory import InMemoryBacktestRunRepository, InMemoryExecutionRuntimeRepository, InMemoryRiskControlsRepository, InMemoryStrategyRepository
from .repositories.postgres_execution import PostgresExecutionRuntimeRepository
from .state import RuntimeState


@dataclass(slots=True)
class ServiceContainer:
    strategy_app: StrategyApplicationService
    backtest_app: BacktestApplicationService
    execution_app: LiveExecutionApplicationService
    operator_queries: OperatorQueryService
    alerts: list


def build_services(app: FastAPI) -> ServiceContainer:
    settings = config_module.settings
    runtime_state = RuntimeState(app.state)
    strategy_repository = InMemoryStrategyRepository(app.state.strategy_registry)
    backtest_repository = InMemoryBacktestRunRepository(app.state.backtest_runs)
    risk_repository = InMemoryRiskControlsRepository(runtime_state, RISK_CONTROLS)
    execution_repository = _build_execution_repository(runtime_state, settings.database_url)
    operator_gateway = OperatorGateway(
        settings_obj=settings,
        default_symbol=settings.backpack_default_symbol,
        default_price_source=PriceSource(settings.backpack_default_price_source),
        market_symbols_list=getattr(app.state, "market_symbols", MARKET_SYMBOLS),
        runtime_state=runtime_state,
        profile_snapshot_cache=getattr(app.state, "live_profile_snapshot_cache", {}),
        profile_snapshot_locks=getattr(app.state, "live_profile_snapshot_locks", {}),
    )
    strategy_app = StrategyApplicationService(strategy_repository)
    backtest_app = BacktestApplicationService(
        strategy_repository=strategy_repository,
        backtest_repository=backtest_repository,
        risk_controls_repository=risk_repository,
        operator_gateway=operator_gateway,
        acceptance_factory=_BacktestAcceptanceFactory(),
        exchange_id="backpack" if settings.backpack_mode == "live" else "mock",
        market_type=settings.backpack_default_market_type if settings.backpack_mode == "live" else "perp",
        demo_mode=settings.backpack_mode == "mock",
    )
    operator_queries = OperatorQueryService(
        gateway=operator_gateway,
        risk_controls_repository=risk_repository,
        settings_obj=settings,
        default_symbol=settings.backpack_default_symbol,
    )
    execution_app = LiveExecutionApplicationService(
        strategy_repository=strategy_repository,
        risk_controls_repository=risk_repository,
        operator_gateway=operator_gateway,
        execution_gateway=BackpackExecutionGateway(
            runtime_state=runtime_state,
            mode=settings.backpack_mode,
        ),
        runtime_repository=execution_repository,
        settings_obj=settings,
    )
    return ServiceContainer(
        strategy_app=strategy_app,
        backtest_app=backtest_app,
        execution_app=execution_app,
        operator_queries=operator_queries,
        alerts=ALERTS,
    )


class _BacktestAcceptanceFactory:
    def build(self, **kwargs):
        return build_backtest_acceptance(**kwargs)


def _build_execution_repository(runtime_state: RuntimeState, database_url: str):
    try:
        return PostgresExecutionRuntimeRepository(database_url=database_url, state=runtime_state)
    except Exception:
        return InMemoryExecutionRuntimeRepository(runtime_state)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    settings = config_module.settings
    app.state.backpack_client = None
    app.state.backpack_provider = None
    app.state.backtest_runs = {"demo": BACKTEST_RESULT}
    app.state.strategy_registry = [item.model_copy(deep=True) for item in STRATEGIES]
    app.state.risk_controls = RISK_CONTROLS.model_copy(deep=True)
    app.state.market_symbols = list(MARKET_SYMBOLS)
    app.state.live_profile_snapshot_cache = {}
    app.state.live_profile_snapshot_locks = {}
    app.state.execution_live_strategies = []
    app.state.execution_orders = []
    app.state.execution_events = []
    app.state.execution_runtime_status = None
    app.state.execution_runtime_task = None

    if settings.backpack_mode == "live":
        client = BackpackClient(
            BackpackAuthConfig(
                base_url=settings.backpack_api_base_url,
                api_key=settings.backpack_api_key or None,
                private_key=settings.backpack_private_key or None,
                window_ms=settings.backpack_window_ms,
            )
        )
        await client.__aenter__()
        app.state.backpack_client = client
        app.state.backpack_provider = BackpackProvider(
            client=client,
            account_label=settings.backpack_account_label,
            market_type=settings.backpack_default_market_type,
            default_price_source=PriceSource(settings.backpack_default_price_source),
        )

    app.state.services = build_services(app)
    try:
        yield
    finally:
        execution_task = getattr(app.state, "execution_runtime_task", None)
        if execution_task is not None:
            execution_task.cancel()
        if app.state.backpack_client is not None:
            await app.state.backpack_client.__aexit__(None, None, None)
