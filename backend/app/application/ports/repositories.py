from __future__ import annotations

from typing import Protocol, Any

from ...domain.shared.enums import PriceSource
from ...domain.strategy.entities import Strategy
from ...schemas import (
    AccountEvent,
    BacktestResult,
    BacktestRunAccepted,
    ExecutionEvent,
    ExecutionOrder,
    ExecutionRuntimeStatus,
    ExchangeAccount,
    KlineResponse,
    LiveStrategyExecution,
    MarketMetric,
    RiskControls,
)
from ...providers.base import AccountSnapshot, NormalizedList, NormalizedRecord


class StrategyRepository(Protocol):
    def list(self) -> list[Strategy]:
        ...

    def get(self, strategy_id: str) -> Strategy | None:
        ...

    def save(self, strategy: Strategy) -> Strategy:
        ...


class BacktestRunRepository(Protocol):
    def get(self, backtest_id: str) -> BacktestResult | None:
        ...

    def save_result(self, result: BacktestResult) -> BacktestResult:
        ...


class RiskControlsRepository(Protocol):
    def get(self) -> RiskControls:
        ...

    def save(self, controls: RiskControls) -> RiskControls:
        ...


class QuantOperatorGateway(Protocol):
    async def fetch_profile_snapshot(self, price_source: PriceSource) -> AccountSnapshot:
        ...

    async def fetch_account_events(self, symbol: str | None = None, limit: int = 100) -> NormalizedList[AccountEvent]:
        ...

    async def fetch_market_pulse(self, symbol: str) -> NormalizedList[MarketMetric]:
        ...

    async def fetch_exchange_accounts(self) -> NormalizedList[ExchangeAccount]:
        ...

    async def fetch_klines(
        self,
        *,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> NormalizedRecord[KlineResponse]:
        ...

    def market_symbols(self) -> list[str]:
        ...


class BacktestAcceptanceFactory(Protocol):
    def build(
        self,
        *,
        backtest_id: str,
        strategy_id: str,
        strategy_kind: str,
        created_at: str,
        demo_mode: bool,
    ) -> BacktestRunAccepted:
        ...


class ExecutionGateway(Protocol):
    async def submit_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool,
        client_order_id: str,
    ) -> ExecutionOrder:
        ...


class ExecutionRuntimeRepository(Protocol):
    def list_live_strategies(self) -> list[LiveStrategyExecution]:
        ...

    def get_live_strategy(self, strategy_id: str) -> LiveStrategyExecution | None:
        ...

    def save_live_strategy(self, item: LiveStrategyExecution) -> LiveStrategyExecution:
        ...

    def append_order(self, order: ExecutionOrder) -> ExecutionOrder:
        ...

    def list_orders(self) -> list[ExecutionOrder]:
        ...

    def append_event(self, event: ExecutionEvent) -> ExecutionEvent:
        ...

    def list_events(self) -> list[ExecutionEvent]:
        ...

    def get_runtime_status(self) -> ExecutionRuntimeStatus:
        ...

    def save_runtime_status(self, status: ExecutionRuntimeStatus) -> ExecutionRuntimeStatus:
        ...

    def get_background_task(self) -> Any | None:
        ...

    def set_background_task(self, task: Any | None) -> None:
        ...
