from __future__ import annotations

from typing import Protocol

from ...domain.shared.enums import PriceSource
from ...domain.strategy.entities import Strategy
from ...schemas import (
    AccountEvent,
    BacktestResult,
    BacktestRunAccepted,
    ExchangeAccount,
    KlineResponse,
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
