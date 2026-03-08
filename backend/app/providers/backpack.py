from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping
from uuid import uuid4

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
from .base import (
    AccountSnapshot,
    BackpackRESTClient,
    MarketPulseSnapshot,
    NormalizedList,
    NormalizedRecord,
    ProviderError,
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
        account_payload = await self.client.get_account()
        capital_payload = await self.client.get_capital()
        collateral_payload = await self.client.get_collateral()
        positions_payload = await self.client.get_positions()

        account = _unwrap_object(account_payload)
        capital_rows = _unwrap_list(capital_payload)
        collateral_rows = _unwrap_list(collateral_payload)
        position_rows = _unwrap_list(positions_payload)

        assets = self._normalize_assets(
            capital_rows=capital_rows,
            collateral_rows=collateral_rows,
            price_source=price_source,
        )
        positions = self._normalize_positions(position_rows, price_source)
        summary = self._normalize_summary(
            account=account,
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
        fills_payload = await self.client.get_fills(symbol=symbol, limit=limit)
        funding_payload = await self.client.get_funding_history(symbol=symbol, limit=limit)

        warnings: list[str] = []
        items: list[NormalizedRecord[AccountEvent]] = []
        for payload in _unwrap_list(fills_payload):
            event, event_warnings = self._normalize_fill_event(payload)
            items.append(NormalizedRecord(data=event, raw_payload=payload, warnings=event_warnings))
            warnings.extend(event_warnings)
        for payload in _unwrap_list(funding_payload):
            event, event_warnings = self._normalize_funding_event(payload)
            items.append(NormalizedRecord(data=event, raw_payload=payload, warnings=event_warnings))
            warnings.extend(event_warnings)

        items.sort(key=lambda item: item.data.occurred_at, reverse=True)
        return NormalizedList(items=items, warnings=warnings)

    async def fetch_market_pulse(
        self,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        price_source: PriceSource,
    ) -> MarketPulseSnapshot:
        market_payload = await self.client.get_market(symbol)
        open_interest_payload = await self.client.get_open_interest(symbol)
        funding_payload = await self.client.get_funding_rates(symbol=symbol)
        klines = await self.fetch_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            price_source=price_source,
        )

        market = _unwrap_object(market_payload)
        open_interest = _unwrap_object(open_interest_payload)
        funding = _unwrap_object(funding_payload)

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
                    value=_stringify_number(_pick(market, "lastPrice", "last_price", "price"), fallback="n/a"),
                    freshness="exchange snapshot",
                    tone="positive",
                ),
                raw_payload=market,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Mark price",
                    value=_stringify_number(_pick(market, "markPrice", "mark_price"), fallback="n/a"),
                    freshness="exchange snapshot",
                ),
                raw_payload=market,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Index price",
                    value=_stringify_number(_pick(market, "indexPrice", "index_price"), fallback="n/a"),
                    freshness="exchange snapshot",
                ),
                raw_payload=market,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Open interest",
                    value=_stringify_number(
                        _pick(open_interest, "openInterest", "open_interest", "oi"),
                        fallback="n/a",
                    ),
                    freshness="60s cadence",
                ),
                raw_payload=open_interest,
            ),
            NormalizedRecord(
                data=MarketMetric(
                    label="Funding rate",
                    value=_stringify_number(
                        _pick(funding, "fundingRate", "funding_rate", "rate"),
                        fallback="n/a",
                    ),
                    freshness="polled",
                ),
                raw_payload=funding,
            ),
        ]
        return MarketPulseSnapshot(metrics=NormalizedList(items=metrics), klines=klines)

    async def fetch_exchange_accounts(self) -> NormalizedList[ExchangeAccount]:
        account_payload = await self.client.get_account()
        account = _unwrap_object(account_payload)
        account_id = _stringify(_pick(account, "id", "accountId", "account_id"), fallback="backpack-account")
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
        rows = _unwrap_list(payload)
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
    ) -> NormalizedRecord[ProfileSummary]:
        total_equity = _sum_values(
            collateral_rows,
            ("collateralValue", "collateral_value", "usdValue", "usd_value", "value"),
        )
        if total_equity == 0:
            total_equity = _floatify(_pick(account, "equity", "accountValue", "account_value"))
        available_margin = _floatify(
            _pick(account, "availableMargin", "available_margin", "availableCollateral", "available_collateral"),
        )
        if available_margin == 0:
            available_margin = _sum_values(
                collateral_rows,
                ("availableValue", "available_value", "availableUsdValue", "available_usd_value"),
            )
        unrealized_pnl = sum(item.data.unrealized_pnl for item in positions.items)
        realized_pnl_24h = _floatify(
            _pick(account, "realizedPnl24h", "realized_pnl_24h", "pnl24h", "dailyPnl", "daily_pnl"),
        )
        win_rate = _floatify(_pick(account, "winRate", "win_rate"))
        synced_at = (
            _coerce_timestamp(_pick(account, "updatedAt", "updated_at", "timestamp"))
            or datetime.now(UTC).isoformat().replace("+00:00", "Z")
        )
        risk_level = _infer_risk_level(total_equity=total_equity, margin=available_margin)
        summary = ProfileSummary(
            total_equity=total_equity,
            available_margin=available_margin,
            unrealized_pnl=unrealized_pnl,
            realized_pnl_24h=realized_pnl_24h,
            win_rate=win_rate,
            risk_level=risk_level,
            price_source=price_source,
            synced_at=synced_at,
        )
        raw_payload = {
            "account": account,
            "collateral": collateral_rows,
            "positions": [item.raw_payload for item in positions.items],
        }
        return NormalizedRecord(data=summary, raw_payload=raw_payload)

    def _normalize_assets(
        self,
        capital_rows: list[Mapping[str, Any]],
        collateral_rows: list[Mapping[str, Any]],
        price_source: PriceSource,
    ) -> NormalizedList[AssetBalance]:
        warnings: list[str] = []
        by_asset: dict[str, dict[str, Any]] = {}
        for row in capital_rows:
            asset = _stringify(_pick(row, "asset", "symbol", "currency"), fallback="UNKNOWN")
            by_asset.setdefault(asset, {}).update({"capital": row})
        for row in collateral_rows:
            asset = _stringify(_pick(row, "asset", "symbol", "currency"), fallback="UNKNOWN")
            by_asset.setdefault(asset, {}).update({"collateral": row})

        total_value = 0.0
        partial_values: dict[str, float] = {}
        for asset, payloads in by_asset.items():
            value = _floatify(
                _pick(
                    payloads.get("collateral", {}),
                    "collateralValue",
                    "collateral_value",
                    "usdValue",
                    "usd_value",
                    "value",
                )
            )
            partial_values[asset] = value
            total_value += value

        items: list[NormalizedRecord[AssetBalance]] = []
        for asset, payloads in by_asset.items():
            capital = payloads.get("capital", {})
            collateral = payloads.get("collateral", {})
            available = _floatify(_pick(capital, "available", "free", "availableBalance", "available_balance"))
            locked = _floatify(_pick(capital, "locked", "hold", "lockedBalance", "locked_balance"))
            collateral_value = partial_values[asset]
            weight = collateral_value / total_value * 100 if total_value else 0.0
            balance = AssetBalance(
                asset=asset,
                available=available,
                locked=locked,
                collateral_value=collateral_value,
                portfolio_weight=weight,
                change_24h=0.0,
                price_source=price_source,
            )
            if not capital:
                warnings.append(f"missing capital payload for asset {asset}")
            items.append(
                NormalizedRecord(
                    data=balance,
                    raw_payload={"capital": capital, "collateral": collateral},
                )
            )
        items.sort(key=lambda item: item.data.collateral_value, reverse=True)
        return NormalizedList(items=items, warnings=warnings)

    def _normalize_positions(
        self,
        rows: list[Mapping[str, Any]],
        price_source: PriceSource,
    ) -> NormalizedList[Position]:
        items: list[NormalizedRecord[Position]] = []
        warnings: list[str] = []
        for row in rows:
            symbol = _normalize_symbol(row)
            quantity = _abs_float(
                _pick(row, "quantity", "qty", "positionQty", "netQuantity", "position_size", "size")
            )
            side = _infer_side(row, quantity)
            mark_price = _floatify(_pick(row, "markPrice", "mark_price", "mark"))
            entry_price = _floatify(_pick(row, "entryPrice", "entry_price", "avgEntryPrice", "average_entry_price"))
            position = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                mark_price=mark_price,
                liquidation_price=_float_or_none(
                    _pick(row, "liquidationPrice", "liquidation_price", "liqPrice", "liquidation")
                ),
                unrealized_pnl=_floatify(_pick(row, "unrealizedPnl", "unrealized_pnl", "uPnl", "pnl")),
                margin_used=_floatify(_pick(row, "marginUsed", "margin_used", "initialMargin", "margin")),
                opened_at=_coerce_timestamp(_pick(row, "openedAt", "opened_at", "createdAt", "created_at")) or "",
                price_source=price_source,
                exchange_extra={
                    "nativeSymbol": _stringify(_pick(row, "symbol", "market", "product"), fallback=symbol),
                    "rawSide": _stringify(_pick(row, "side"), fallback=side),
                    "positionId": _stringify(_pick(row, "id", "positionId", "position_id"), fallback=""),
                },
            )
            if not symbol or symbol == "UNKNOWN":
                warnings.append("position missing symbol")
            items.append(NormalizedRecord(data=position, raw_payload=row))
        items.sort(key=lambda item: item.data.unrealized_pnl, reverse=True)
        return NormalizedList(items=items, warnings=warnings)

    def _normalize_fill_event(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[AccountEvent, list[str]]:
        warnings: list[str] = []
        raw_type = _stringify(
            _pick(payload, "fillType", "fill_type", "eventType", "event_type", "type"),
            fallback="trade_fill",
        ).lower()
        event_type = _map_event_type(raw_type)
        origin = _map_origin(_stringify(_pick(payload, "source", "origin"), fallback="system"))
        amount = _floatify(_pick(payload, "quantity", "qty", "size", "amount"))
        if amount == 0 and event_type == EventType.FEE_CHARGE:
            amount = -_floatify(_pick(payload, "fee", "feeAmount", "fee_amount"))
        asset = _stringify(_pick(payload, "asset", "baseAsset", "base_asset", "feeAsset", "fee_asset"), fallback="USDC")
        occurred_at = _coerce_timestamp(_pick(payload, "timestamp", "time", "createdAt", "created_at"))
        if not occurred_at:
            warnings.append("fill event missing timestamp")
            occurred_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        event = AccountEvent(
            id=_stringify(_pick(payload, "id", "fillId", "fill_id"), fallback=f"fill-{uuid4().hex}"),
            event_type=event_type,
            origin=origin,
            asset=asset,
            amount=amount,
            pnl_effect=_floatify(_pick(payload, "realizedPnl", "realized_pnl", "pnlEffect", "pnl_effect")),
            position_effect=_describe_position_effect(payload, fallback="Fill event"),
            occurred_at=occurred_at,
        )
        return event, warnings

    def _normalize_funding_event(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[AccountEvent, list[str]]:
        occurred_at = _coerce_timestamp(_pick(payload, "timestamp", "time", "settledAt", "settled_at"))
        warnings: list[str] = []
        if not occurred_at:
            warnings.append("funding event missing timestamp")
            occurred_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        amount = _floatify(_pick(payload, "amount", "payment", "fundingPayment", "funding_payment"))
        symbol = _normalize_symbol(payload)
        event = AccountEvent(
            id=_stringify(_pick(payload, "id", "fundingId", "funding_id"), fallback=f"funding-{uuid4().hex}"),
            event_type=EventType.FUNDING_SETTLEMENT,
            origin=EventOrigin.SYSTEM,
            asset=_stringify(_pick(payload, "asset", "currency"), fallback="USDC"),
            amount=amount,
            pnl_effect=amount,
            position_effect=f"Funding settlement on {symbol}",
            occurred_at=occurred_at,
        )
        return event, warnings

    def _normalize_candle(
        self,
        payload: Mapping[str, Any],
    ) -> tuple[Candle, list[str]]:
        warnings: list[str] = []
        timestamp = _coerce_timestamp(_pick(payload, "timestamp", "time", "t", "startTime", "start_time"))
        if not timestamp:
            warnings.append("kline missing timestamp")
            timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        candle = Candle(
            timestamp=timestamp,
            open=_floatify(_pick(payload, "open", "o")),
            high=_floatify(_pick(payload, "high", "h")),
            low=_floatify(_pick(payload, "low", "l")),
            close=_floatify(_pick(payload, "close", "c")),
            volume=_floatify(_pick(payload, "volume", "v")),
        )
        return candle, warnings


def _unwrap_object(payload: Any) -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        for key in ("data", "result"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                return nested
            if isinstance(nested, list) and nested and isinstance(nested[0], Mapping):
                return nested[0]
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], Mapping):
        return payload[0]
    return {}


def _unwrap_list(payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("items", "rows", "results", "data", "result"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, Mapping)]
        return [payload]
    return []


def _pick(payload: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _floatify(value: Any) -> float:
    if value in (None, "", False):
        return 0.0
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _float_or_none(value: Any) -> float | None:
    if value in (None, "", False):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _abs_float(value: Any) -> float:
    return abs(_floatify(value))


def _stringify(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _stringify_number(value: Any, fallback: str = "") -> str:
    if value in (None, ""):
        return fallback
    if isinstance(value, (int, float)):
        return str(value)
    return _stringify(value, fallback=fallback)


def _normalize_symbol(payload: Mapping[str, Any]) -> str:
    return _stringify(
        _pick(payload, "symbol", "market", "product", "productId", "instrument", "name"),
        fallback="UNKNOWN",
    )


def _infer_side(payload: Mapping[str, Any], quantity: float) -> str:
    raw_side = _stringify(_pick(payload, "side"), fallback="").lower()
    if raw_side in {"long", "short"}:
        return raw_side
    signed_qty = _floatify(_pick(payload, "netQuantity", "net_quantity", "quantity", "qty", "size"))
    if signed_qty < 0:
        return "short"
    if signed_qty > 0:
        return "long"
    return "long" if quantity >= 0 else "short"


def _coerce_timestamp(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.endswith("Z"):
            return stripped
        if stripped.isdigit():
            value = int(stripped)
        else:
            try:
                parsed = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
                return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
            except ValueError:
                return stripped
    if isinstance(value, (int, float)):
        number = float(value)
        if number > 1_000_000_000_000_000:
            number /= 1_000_000
        elif number > 1_000_000_000_000:
            number /= 1_000
        elif number > 10_000_000_000:
            number /= 1_000
        return datetime.fromtimestamp(number, tz=UTC).isoformat().replace("+00:00", "Z")
    return None


def _sum_values(rows: list[Mapping[str, Any]], keys: tuple[str, ...]) -> float:
    total = 0.0
    for row in rows:
        total += _floatify(_pick(row, *keys))
    return total


def _map_event_type(raw_type: str) -> EventType:
    normalized = raw_type.lower()
    if "liquid" in normalized:
        return EventType.LIQUIDATION
    if "adl" in normalized:
        return EventType.ADL
    if "conversion" in normalized or "collateral" in normalized:
        return EventType.COLLATERAL_CONVERSION
    if "funding" in normalized:
        return EventType.FUNDING_SETTLEMENT
    if "fee" in normalized:
        return EventType.FEE_CHARGE
    if "deposit" in normalized:
        return EventType.DEPOSIT
    if "withdraw" in normalized:
        return EventType.WITHDRAWAL
    if "manual" in normalized:
        return EventType.MANUAL_ADJUSTMENT
    return EventType.TRADE_FILL


def _map_origin(raw_origin: str) -> EventOrigin:
    normalized = raw_origin.lower()
    if "strategy" in normalized or "algo" in normalized:
        return EventOrigin.STRATEGY
    if "manual" in normalized or "user" in normalized:
        return EventOrigin.MANUAL
    if "risk" in normalized or "liquid" in normalized or "adl" in normalized:
        return EventOrigin.RISK
    return EventOrigin.SYSTEM


def _describe_position_effect(payload: Mapping[str, Any], fallback: str) -> str:
    symbol = _normalize_symbol(payload)
    side = _stringify(_pick(payload, "side"), fallback="").lower()
    quantity = _stringify_number(_pick(payload, "quantity", "qty", "size"), fallback="")
    if symbol != "UNKNOWN" and quantity:
        descriptor = f"{side} {quantity}".strip()
        return f"{fallback} on {symbol} {descriptor}".strip()
    if symbol != "UNKNOWN":
        return f"{fallback} on {symbol}"
    return fallback


def _infer_risk_level(total_equity: float, margin: float) -> str:
    if total_equity <= 0:
        return "unknown"
    usage = 1 - (margin / total_equity if total_equity else 0)
    if usage >= 0.75:
        return "elevated"
    if usage >= 0.45:
        return "managed"
    return "disciplined"
