from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping

from ..schemas import (
    AccountEvent,
    AssetBalance,
    Candle,
    EventOrigin,
    EventType,
    ExchangeAccount,
    KlineResponse,
    MarketMetric,
    Position,
    PriceSource,
    ProfileSummary,
)
from ..backpack import BackpackRequestError
from .base import (
    AccountSnapshot,
    BackpackRESTClient,
    MarketPulseSnapshot,
    NormalizedList,
    NormalizedRecord,
    ProviderError,
)
from .backpack_helpers import (
    coerce_timestamp as _coerce_timestamp,
    float_or_none as _float_or_none,
    floatify as _floatify,
    format_rate_percent as _format_rate_percent,
    infer_side as _infer_side,
    map_event_type as _map_event_type,
    normalize_symbol as _normalize_symbol,
    pick as _pick,
    pick_latest_object as _pick_latest_object,
    require_float as _require_float,
    stringify as _stringify,
    stringify_number as _stringify_number,
    unwrap_list as _unwrap_list,
    unwrap_object as _unwrap_object,
)
from .backpack_mapper import (
    normalize_assets,
    normalize_candle,
    normalize_capital_rows,
    normalize_collateral_payload,
    normalize_fill_event,
    normalize_funding_event,
    normalize_positions,
    normalize_summary,
)


@dataclass(slots=True)
class BackpackProvider:
    client: BackpackRESTClient
    account_label: str = "backpack-primary"
    market_type: str = "perp"
    default_price_source: PriceSource = PriceSource.MARK

    async def fetch_account_snapshot(
        self,
        price_source: PriceSource = PriceSource.MARK,
    ) -> AccountSnapshot:
        (
            account_payload,
            capital_payload,
            collateral_payload,
            positions_payload,
        ) = await asyncio.gather(
            self.client.get_account(),
            self.client.get_capital(),
            self.client.get_collateral(),
            self.client.get_positions(),
        )

        account = _unwrap_object(account_payload, context="backpack account")
        capital_rows = self._normalize_capital_rows(capital_payload)
        collateral_object, collateral_rows = self._normalize_collateral_payload(collateral_payload)
        position_rows = _unwrap_list(positions_payload, context="backpack positions")

        assets = self._normalize_assets(
            capital_rows=capital_rows,
            collateral_rows=collateral_rows,
            price_source=price_source,
        )
        positions = self._normalize_positions(position_rows, price_source)
        summary = self._normalize_summary(
            account=account,
            collateral=collateral_object,
            collateral_rows=collateral_rows,
            positions=positions,
            price_source=price_source,
        )
        return AccountSnapshot(summary=summary, assets=assets, positions=positions)

    async def fetch_account_events(
        self,
        symbol: str | None = None,
        limit: int = 100,
    ) -> NormalizedList[AccountEvent]:
        fills_payload, funding_payload = await asyncio.gather(
            self.client.get_fills(symbol=symbol, limit=limit),
            self.client.get_funding_history(symbol=symbol, limit=limit),
            return_exceptions=True,
        )

        warnings: list[str] = []
        items: list[NormalizedRecord[AccountEvent]] = []
        fill_rows = self._unwrap_history_or_empty(fills_payload, context="backpack fills", warnings=warnings)
        funding_rows = self._unwrap_history_or_empty(
            funding_payload,
            context="backpack funding history",
            warnings=warnings,
        )
        for payload in fill_rows:
            event, event_warnings = self._normalize_fill_event(payload)
            items.append(NormalizedRecord(data=event, raw_payload=payload, warnings=event_warnings))
            warnings.extend(event_warnings)
        for payload in funding_rows:
            event, event_warnings = self._normalize_funding_event(payload)
            items.append(NormalizedRecord(data=event, raw_payload=payload, warnings=event_warnings))
            warnings.extend(event_warnings)

        items.sort(key=lambda item: item.data.occurred_at, reverse=True)
        return NormalizedList(items=items, warnings=warnings)

    async def fetch_market_pulse(
        self,
        symbol: str,
        price_source: PriceSource,
        interval: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        include_klines: bool = False,
    ) -> MarketPulseSnapshot:
        kline_interval = interval or "1m"
        now_seconds = int(datetime.now(tz=UTC).timestamp())
        recent_start = max(now_seconds - 3600, 0)

        fetches = await asyncio.gather(
            self._fetch_ticker_payload(symbol),
            self.client.get_open_interest(symbol),
            self.client.get_funding_rates(symbol=symbol),
            *(
                [
                    self.fetch_klines(
                        symbol=symbol,
                        interval=kline_interval,
                        start_time=recent_start,
                        end_time=now_seconds,
                        price_source=PriceSource.MARK,
                    ),
                    self.fetch_klines(
                        symbol=symbol,
                        interval=kline_interval,
                        start_time=recent_start,
                        end_time=now_seconds,
                        price_source=PriceSource.INDEX,
                    ),
                ]
                if include_klines
                else []
            ),
        )
        ticker_payload, open_interest_payload, funding_payload = fetches[:3]
        mark_klines = fetches[3] if include_klines else None
        index_klines = fetches[4] if include_klines else None
        klines = None
        if include_klines:
            if interval is None or start_time is None or end_time is None:
                raise ValueError("interval, start_time, and end_time are required when include_klines is true.")
            klines = await self.fetch_klines(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                price_source=price_source,
            )

        ticker = _pick_latest_object(ticker_payload, context=f"backpack ticker {symbol}")
        open_interest = _pick_latest_object(open_interest_payload, context=f"backpack open interest {symbol}")
        funding = _pick_latest_object(funding_payload, context=f"backpack funding rate {symbol}")
        mark_price = _float_or_none(_pick(ticker, "markPrice", "mark_price")) or (
            _latest_candle_close(mark_klines, context=f"backpack mark klines {symbol}") if mark_klines else None
        )
        index_price = _float_or_none(_pick(ticker, "indexPrice", "index_price")) or (
            _latest_candle_close(index_klines, context=f"backpack index klines {symbol}") if index_klines else None
        )

        metrics = [
            NormalizedRecord(
                data=MarketMetric(
                    label=f"{symbol} price source",
                    value=str(price_source.value).upper(),
                    freshness="request-scoped",
                    tone="positive",
                ),
                raw_payload={"symbol": symbol, "priceSource": price_source.value},
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Last price",
                    value=_stringify_number(
                        _require_float(
                            ticker,
                            "lastPrice",
                            "last_price",
                            "price",
                            "close",
                            context=f"backpack market {symbol}",
                        ),
                    ),
                    freshness="exchange snapshot",
                    tone="positive",
                ),
                raw_payload=ticker,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Mark price",
                    value=_stringify_number(mark_price or 0.0),
                    freshness="exchange snapshot",
                ),
                raw_payload=mark_klines.raw_payload if mark_klines else ticker,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Index price",
                    value=_stringify_number(index_price or 0.0),
                    freshness="exchange snapshot",
                ),
                raw_payload=index_klines.raw_payload if index_klines else ticker,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Open interest",
                    value=_stringify_number(
                        _require_float(
                            open_interest,
                            "openInterest",
                            "open_interest",
                            "oi",
                            context=f"backpack open interest {symbol}",
                        ),
                    ),
                    freshness="60s cadence",
                ),
                raw_payload=open_interest,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Funding rate",
                    value=_format_rate_percent(
                        _require_float(
                            funding,
                            "fundingRate",
                            "funding_rate",
                            "rate",
                            context=f"backpack funding rate {symbol}",
                        )
                    ),
                    freshness="polled",
                ),
                raw_payload=funding,
            ),
        ]
        return MarketPulseSnapshot(metrics=NormalizedList(items=metrics), klines=klines)

    async def fetch_exchange_accounts(self) -> NormalizedList[ExchangeAccount]:
        account_payload = await self.client.get_account()
        account = _unwrap_object(account_payload, context="backpack account")
        account_id = _stringify(
            _pick(account, "id", "accountId", "account_id"),
            fallback=f"{self.account_label}:{self.market_type}",
        )
        status = "healthy" if account else "attention"
        rotation_time = _coerce_timestamp(_pick(account, "updatedAt", "updated_at", "createdAt", "created_at"))
        record = ExchangeAccount(
            id=account_id,
            exchange="backpack",
            label=_stringify(_pick(account, "label", "name"), fallback=self.account_label),
            market_type=_stringify(_pick(account, "marketType", "market_type"), fallback=self.market_type),
            last_credential_rotation=rotation_time or "",
            status=status,
        )
        return NormalizedList(items=[NormalizedRecord(data=record, raw_payload=account)])

    async def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> NormalizedRecord[KlineResponse]:
        payload = await self.client.get_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            price_source=price_source,
        )
        rows = _unwrap_list(payload, context=f"backpack klines {symbol}")
        candles: list[Candle] = []
        warnings: list[str] = []
        for row in rows:
            candle, candle_warnings = self._normalize_candle(row)
            candles.append(candle)
            warnings.extend(candle_warnings)

        response = KlineResponse(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            price_source=price_source,
            candles=candles,
        )
        return NormalizedRecord(data=response, raw_payload={"items": rows}, warnings=warnings)

    def _normalize_summary(
        self,
        account: Mapping[str, Any],
        collateral_rows: list[Mapping[str, Any]],
        positions: NormalizedList[Position],
        price_source: PriceSource,
        collateral: Mapping[str, Any] | None = None,
    ) -> NormalizedRecord[ProfileSummary]:
        return normalize_summary(
            account=account,
            collateral_rows=collateral_rows,
            positions=positions,
            price_source=price_source,
            collateral=collateral,
        )

    def _normalize_collateral_payload(
        self,
        collateral_payload: Any,
    ) -> tuple[Mapping[str, Any], list[Mapping[str, Any]]]:
        return normalize_collateral_payload(collateral_payload)

    async def _fetch_ticker_payload(self, symbol: str):
        get_ticker = getattr(self.client, "get_ticker", None)
        if callable(get_ticker):
            return await get_ticker(symbol)
        get_market = getattr(self.client, "get_market", None)
        if callable(get_market):
            return await get_market(symbol)
        raise AttributeError("Backpack REST client must provide get_ticker() or get_market().")

    def _normalize_capital_rows(self, capital_payload: Any) -> list[Mapping[str, Any]]:
        return normalize_capital_rows(capital_payload)

    def _unwrap_history_or_empty(
        self,
        payload: Any,
        *,
        context: str,
        warnings: list[str],
    ) -> list[Mapping[str, Any]]:
        if isinstance(payload, BackpackRequestError) and payload.status_code == 400:
            warnings.append(f"{context} unavailable for this account; treating as empty history")
            return []
        if isinstance(payload, Exception):
            raise payload
        return _unwrap_list(payload, context=context)

    def _normalize_assets(
        self,
        capital_rows: list[Mapping[str, Any]],
        collateral_rows: list[Mapping[str, Any]],
        price_source: PriceSource,
    ) -> NormalizedList[AssetBalance]:
        return normalize_assets(
            capital_rows=capital_rows,
            collateral_rows=collateral_rows,
            price_source=price_source,
        )

    def _normalize_positions(
        self,
        rows: list[Mapping[str, Any]],
        price_source: PriceSource,
    ) -> NormalizedList[Position]:
        return normalize_positions(rows, price_source)

    def _normalize_fill_event(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[AccountEvent, list[str]]:
        return normalize_fill_event(payload)

    def _normalize_funding_event(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[AccountEvent, list[str]]:
        return normalize_funding_event(payload)

    def _normalize_candle(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[Candle, list[str]]:
        return normalize_candle(payload)


def _latest_candle_close(payload: NormalizedRecord[KlineResponse], *, context: str) -> float:
    candles = payload.data.candles
    if not candles:
        raise ProviderError(f"{context} expected at least one candle")
    return candles[-1].close
