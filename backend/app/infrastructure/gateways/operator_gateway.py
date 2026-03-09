from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from ...application.errors import ApplicationError, from_backpack_request_error
from ...application.ports.repositories import QuantOperatorGateway
from ...backpack import BackpackAuthError, BackpackRequestError
from ...domain.shared.enums import PriceSource
from ...mock_data import ACCOUNT_EVENTS, ASSET_BALANCES, EXCHANGE_ACCOUNTS, MARKET_PULSE, MARKET_SYMBOLS, POSITIONS, PROFILE_SUMMARY, _generate_candles
from ...providers import ProviderError
from ...providers.base import AccountSnapshot, MarketPulseSnapshot, NormalizedList, NormalizedRecord
from ...schemas import AccountEvent, AssetBalance, ExchangeAccount, KlineResponse, MarketMetric, Position
from ..state import RuntimeState


LIVE_PROFILE_SNAPSHOT_TTL_SECONDS = 1.0


@dataclass(slots=True)
class OperatorGateway(QuantOperatorGateway):
    settings_obj: Any
    default_symbol: str
    default_price_source: PriceSource
    market_symbols_list: list[str]
    runtime_state: RuntimeState = field(default_factory=lambda: RuntimeState(object()))
    profile_snapshot_cache: dict[str, dict[str, Any]] = field(default_factory=dict)
    profile_snapshot_locks: dict[str, asyncio.Lock] = field(default_factory=dict)

    async def fetch_profile_snapshot(self, price_source: PriceSource) -> AccountSnapshot:
        if self.mode != "live":
            return _build_mock_profile_snapshot()

        cache_key = price_source.value
        entry = self.profile_snapshot_cache.get(cache_key)
        now = time.monotonic()
        if entry is not None and entry["expires_at"] > now:
            return entry["snapshot"]

        lock = self.profile_snapshot_locks.setdefault(cache_key, asyncio.Lock())
        async with lock:
            entry = self.profile_snapshot_cache.get(cache_key)
            now = time.monotonic()
            if entry is not None and entry["expires_at"] > now:
                return entry["snapshot"]
            snapshot = await self._provider_call(
                lambda provider: provider.fetch_account_snapshot(price_source=price_source)
            )
            self.profile_snapshot_cache[cache_key] = {
                "snapshot": snapshot,
                "expires_at": now + LIVE_PROFILE_SNAPSHOT_TTL_SECONDS,
            }
            return snapshot

    async def fetch_account_events(self, symbol: str | None = None, limit: int = 100) -> NormalizedList[AccountEvent]:
        if self.mode != "live":
            return _build_mock_account_events()
        return await self._provider_call(lambda provider: provider.fetch_account_events(symbol=symbol, limit=limit))

    async def fetch_market_pulse(self, symbol: str) -> NormalizedList[MarketMetric]:
        if self.mode != "live":
            return _build_mock_market_pulse(symbol).metrics
        snapshot = await self._provider_call(
            lambda provider: provider.fetch_market_pulse(
                symbol=symbol,
                price_source=self.default_price_source,
                include_klines=False,
            )
        )
        return snapshot.metrics

    async def fetch_exchange_accounts(self) -> NormalizedList[ExchangeAccount]:
        if self.mode != "live":
            return _build_mock_exchange_accounts()
        return await self._provider_call(lambda provider: provider.fetch_exchange_accounts())

    async def fetch_klines(
        self,
        *,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> NormalizedRecord[KlineResponse]:
        if self.mode == "live":
            return await self._provider_call(
                lambda provider: provider.fetch_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=start_time,
                    end_time=end_time,
                    price_source=price_source,
                )
            )

        seed = sum(ord(char) for char in f"{symbol}:{interval}:{price_source}:{start_time}:{end_time}")
        return NormalizedRecord(
            data=KlineResponse(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                price_source=price_source,
                candles=_generate_candles(
                    symbol=symbol,
                    seed=seed,
                    request=type(
                        "BacktestRequestLike",
                        (),
                        {
                            "symbol": symbol,
                            "interval": interval,
                            "start_time": start_time,
                            "end_time": end_time,
                            "price_source": price_source,
                            "fee_bps": 0,
                            "slippage_bps": 0,
                        },
                    )(),
                ),
            ),
            raw_payload={"symbol": symbol, "interval": interval},
        )

    def market_symbols(self) -> list[str]:
        return list(self.market_symbols_list)

    async def _provider_call(self, callback: Callable[[Any], Awaitable[Any]]):
        if self.provider is None:
            raise ApplicationError(
                code="provider_not_initialized",
                message="Backpack live provider is not initialized.",
                status_code=503,
                retryable=True,
                provider="backpack",
            )
        try:
            return await callback(self.provider)
        except BackpackAuthError as exc:
            raise ApplicationError(
                code="provider_auth_error",
                message=str(exc),
                status_code=503,
                retryable=False,
                provider="backpack",
            ) from exc
        except BackpackRequestError as exc:
            raise from_backpack_request_error(exc) from exc
        except ProviderError as exc:
            raise ApplicationError(
                code="provider_response_invalid",
                message=str(exc),
                status_code=502,
                retryable=False,
                provider="backpack",
            ) from exc
        except ValueError as exc:
            raise ApplicationError(code="invalid_request", message=str(exc), status_code=400) from exc

    @property
    def provider(self) -> Any | None:
        return self.runtime_state.get("backpack_provider")

    @property
    def mode(self) -> str:
        return str(self.settings_obj.backpack_mode)


def _build_mock_profile_snapshot() -> AccountSnapshot:
    return AccountSnapshot(
        summary=NormalizedRecord(data=PROFILE_SUMMARY, raw_payload=PROFILE_SUMMARY.model_dump(by_alias=True)),
        assets=NormalizedList(
            items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in ASSET_BALANCES]
        ),
        positions=NormalizedList(
            items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in POSITIONS]
        ),
    )


def _build_mock_account_events() -> NormalizedList[AccountEvent]:
    return NormalizedList(
        items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in ACCOUNT_EVENTS]
    )


def _build_mock_market_pulse(symbol: str) -> MarketPulseSnapshot:
    base = symbol.split("_", 1)[0]
    return MarketPulseSnapshot(
        metrics=NormalizedList(
            items=[
                NormalizedRecord(
                    data=item.model_copy(update={"label": item.label.replace("BTC", base)}),
                    raw_payload=item.model_dump(by_alias=True),
                )
                for item in MARKET_PULSE
            ]
        )
    )


def _build_mock_exchange_accounts() -> NormalizedList[ExchangeAccount]:
    return NormalizedList(
        items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in EXCHANGE_ACCOUNTS]
    )
