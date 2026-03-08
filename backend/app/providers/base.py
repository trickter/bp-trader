from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Mapping, Protocol, TypeVar

from ..schemas import (
    AccountEvent,
    AssetBalance,
    ExchangeAccount,
    KlineResponse,
    MarketMetric,
    Position,
    PriceSource,
    ProfileSummary,
)

T = TypeVar("T")


class ProviderError(RuntimeError):
    """Raised when exchange data cannot be normalized safely."""


@dataclass(slots=True)
class NormalizedRecord(Generic[T]):
    data: T
    raw_payload: Mapping[str, Any]
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class NormalizedList(Generic[T]):
    items: list[NormalizedRecord[T]]
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AccountSnapshot:
    summary: NormalizedRecord[ProfileSummary]
    assets: NormalizedList[AssetBalance]
    positions: NormalizedList[Position]


@dataclass(slots=True)
class MarketPulseSnapshot:
    metrics: NormalizedList[MarketMetric]
    klines: NormalizedRecord[KlineResponse] | None = None


class BackpackRESTClient(Protocol):
    async def get_account(self) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_capital(self) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_collateral(self) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_positions(
        self,
        symbol: str | None = None,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_fills(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_funding_history(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_markets(self) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_market(self, symbol: str) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_ticker(
        self,
        symbol: str,
        interval: str | None = None,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_open_interest(self, symbol: str) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_funding_rates(
        self,
        symbol: str | None = None,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        ...


class QuantDataProvider(Protocol):
    async def fetch_account_snapshot(
        self,
        price_source: PriceSource = PriceSource.MARK,
    ) -> AccountSnapshot:
        ...

    async def fetch_account_events(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> NormalizedList[AccountEvent]:
        ...

    async def fetch_market_pulse(
        self,
        symbol: str,
        price_source: PriceSource,
        interval: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        include_klines: bool = False,
    ) -> MarketPulseSnapshot:
        ...

    async def fetch_exchange_accounts(self) -> NormalizedList[ExchangeAccount]:
        ...

    async def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> NormalizedRecord[KlineResponse]:
        ...
