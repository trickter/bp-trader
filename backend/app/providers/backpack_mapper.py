from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from ..schemas import AccountEvent, AssetBalance, Candle, EventOrigin, EventType, Position, PriceSource, ProfileSummary
from .base import NormalizedList, NormalizedRecord, ProviderError
from .backpack_helpers import (
    coerce_timestamp,
    describe_position_effect,
    float_or_none,
    floatify,
    infer_risk_level,
    infer_side,
    map_event_type,
    map_origin,
    pick,
    require_float,
    require_string,
    require_symbol,
    require_timestamp,
    stringify,
    stringify_number,
    sum_values,
    unwrap_list,
    unwrap_object,
)


def normalize_summary(
    *,
    account: Mapping[str, Any],
    collateral_rows: list[Mapping[str, Any]],
    positions: NormalizedList[Position],
    price_source: PriceSource,
    collateral: Mapping[str, Any] | None = None,
) -> NormalizedRecord[ProfileSummary]:
    collateral = collateral or {}
    total_equity = sum_values(collateral_rows, ("collateralValue", "collateral_value", "usdValue", "usd_value", "value"))
    if total_equity == 0:
        total_equity = float_or_none(pick(collateral, "assetsValue", "assets_value", "accountValue", "account_value", "equity")) or float_or_none(
            pick(account, "equity", "accountValue", "account_value")
        ) or 0.0
    available_margin = float_or_none(
        pick(collateral, "availableCollateral", "available_collateral", "availableMargin", "available_margin")
    )
    if available_margin is None:
        available_margin = float_or_none(
            pick(account, "availableMargin", "available_margin", "availableCollateral", "available_collateral")
        ) or sum_values(collateral_rows, ("availableValue", "available_value", "availableUsdValue", "available_usd_value"))
    unrealized_pnl = sum(item.data.unrealized_pnl for item in positions.items)
    realized_pnl_24h = floatify(pick(account, "realizedPnl24h", "realized_pnl_24h", "pnl24h", "dailyPnl", "daily_pnl"))
    win_rate = floatify(pick(account, "winRate", "win_rate"))
    synced_at = (
        coerce_timestamp(pick(account, "updatedAt", "updated_at", "timestamp"))
        or coerce_timestamp(pick(collateral, "updatedAt", "updated_at", "timestamp"))
        or datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    )
    return NormalizedRecord(
        data=ProfileSummary(
            total_equity=total_equity,
            available_margin=available_margin,
            unrealized_pnl=unrealized_pnl,
            realized_pnl_24h=realized_pnl_24h,
            win_rate=win_rate,
            risk_level=infer_risk_level(total_equity=total_equity, margin=available_margin),
            price_source=price_source,
            synced_at=synced_at,
        ),
        raw_payload={
            "account": account,
            "collateralSummary": collateral,
            "collateral": collateral_rows,
            "positions": [item.raw_payload for item in positions.items],
        },
    )


def normalize_collateral_payload(collateral_payload: Any) -> tuple[Mapping[str, Any], list[Mapping[str, Any]]]:
    if isinstance(collateral_payload, list):
        return {"collateral": collateral_payload}, unwrap_list(collateral_payload, context="backpack collateral rows")
    collateral_object = unwrap_object(collateral_payload, context="backpack collateral")
    nested_rows = pick(collateral_object, "collateral", "items", "assets", "balances")
    if nested_rows is None:
        return collateral_object, []
    return collateral_object, unwrap_list(nested_rows, context="backpack collateral rows")


def normalize_capital_rows(capital_payload: Any) -> list[Mapping[str, Any]]:
    if isinstance(capital_payload, Mapping):
        rows: list[Mapping[str, Any]] = []
        for asset, values in capital_payload.items():
            if not isinstance(values, Mapping):
                raise ProviderError("backpack capital payload contained a non-object asset row")
            rows.append({"asset": asset, **values})
        return rows
    return unwrap_list(capital_payload, context="backpack capital")


def normalize_assets(
    *,
    capital_rows: list[Mapping[str, Any]],
    collateral_rows: list[Mapping[str, Any]],
    price_source: PriceSource,
) -> NormalizedList[AssetBalance]:
    warnings: list[str] = []
    by_asset: dict[str, dict[str, Any]] = {}
    for row in capital_rows:
        asset = require_string(row, "asset", "symbol", "currency", context="backpack capital asset")
        by_asset.setdefault(asset, {}).update({"capital": row})
    for row in collateral_rows:
        asset = require_string(row, "asset", "symbol", "currency", context="backpack collateral asset")
        by_asset.setdefault(asset, {}).update({"collateral": row})

    total_value = 0.0
    partial_values: dict[str, float] = {}
    for asset, payloads in by_asset.items():
        if payloads.get("collateral"):
            value = require_float(
                payloads["collateral"],
                "collateralValue",
                "collateral_value",
                "usdValue",
                "usd_value",
                "value",
                context=f"backpack collateral asset {asset}",
            )
        else:
            value = 0.0
        partial_values[asset] = value
        total_value += value

    items: list[NormalizedRecord[AssetBalance]] = []
    for asset, payloads in by_asset.items():
        capital = payloads.get("capital", {})
        collateral = payloads.get("collateral", {})
        available = floatify(pick(capital, "available", "free", "availableBalance", "available_balance"))
        locked = floatify(pick(capital, "locked", "hold", "lockedBalance", "locked_balance"))
        collateral_value = partial_values[asset]
        weight = collateral_value / total_value * 100 if total_value else 0.0
        if not capital:
            warnings.append(f"missing capital payload for asset {asset}")
        items.append(
            NormalizedRecord(
                data=AssetBalance(
                    asset=asset,
                    available=available,
                    locked=locked,
                    collateral_value=collateral_value,
                    portfolio_weight=weight,
                    change_24h=0.0,
                    price_source=price_source,
                ),
                raw_payload={"capital": capital, "collateral": collateral},
            )
        )
    items.sort(key=lambda item: item.data.collateral_value, reverse=True)
    return NormalizedList(items=items, warnings=warnings)


def normalize_positions(rows: list[Mapping[str, Any]], price_source: PriceSource) -> NormalizedList[Position]:
    items: list[NormalizedRecord[Position]] = []
    for row in rows:
        symbol = require_symbol(row, context="backpack position")
        quantity = abs(require_float(row, "quantity", "qty", "positionQty", "netQuantity", "position_size", "size", context=f"backpack position {symbol}"))
        side = infer_side(row, quantity)
        items.append(
            NormalizedRecord(
                data=Position(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    entry_price=require_float(row, "entryPrice", "entry_price", "avgEntryPrice", "average_entry_price", context=f"backpack position {symbol}"),
                    mark_price=require_float(row, "markPrice", "mark_price", "mark", context=f"backpack position {symbol}"),
                    liquidation_price=float_or_none(pick(row, "liquidationPrice", "liquidation_price", "liqPrice", "liquidation")),
                    unrealized_pnl=floatify(pick(row, "unrealizedPnl", "unrealized_pnl", "uPnl", "pnl")),
                    margin_used=floatify(pick(row, "marginUsed", "margin_used", "initialMargin", "margin")),
                    opened_at=coerce_timestamp(pick(row, "openedAt", "opened_at", "createdAt", "created_at")) or "",
                    price_source=price_source,
                    exchange_extra={
                        "nativeSymbol": stringify(pick(row, "symbol", "market", "product"), fallback=symbol),
                        "rawSide": stringify(pick(row, "side"), fallback=side),
                        "positionId": stringify(pick(row, "id", "positionId", "position_id"), fallback=""),
                    },
                ),
                raw_payload=row,
            )
        )
    items.sort(key=lambda item: item.data.unrealized_pnl, reverse=True)
    return NormalizedList(items=items, warnings=[])


def normalize_fill_event(payload: Mapping[str, Any]) -> tuple[AccountEvent, list[str]]:
    raw_type = require_string(payload, "fillType", "fill_type", "eventType", "event_type", "type", context="backpack fill").lower()
    event_type = map_event_type(raw_type)
    origin = map_origin(stringify(pick(payload, "source", "origin"), fallback="system"))
    amount = float_or_none(pick(payload, "quantity", "qty", "size", "amount"))
    if amount == 0 and event_type == EventType.FEE_CHARGE:
        amount = None
    if amount is None and event_type == EventType.FEE_CHARGE:
        amount = -require_float(payload, "fee", "feeAmount", "fee_amount", context="backpack fill")
    if amount is None:
        raise ProviderError("backpack fill missing required field: quantity/qty/size/amount")
    return (
        AccountEvent(
            id=require_string(payload, "id", "fillId", "fill_id", context="backpack fill"),
            event_type=event_type,
            origin=origin,
            asset=require_string(payload, "asset", "baseAsset", "base_asset", "feeAsset", "fee_asset", context="backpack fill"),
            amount=amount,
            pnl_effect=floatify(pick(payload, "realizedPnl", "realized_pnl", "pnlEffect", "pnl_effect")),
            position_effect=describe_position_effect(payload, fallback="Fill event"),
            occurred_at=require_timestamp(payload, "timestamp", "time", "createdAt", "created_at", context="backpack fill"),
        ),
        [],
    )


def normalize_funding_event(payload: Mapping[str, Any]) -> tuple[AccountEvent, list[str]]:
    symbol = require_symbol(payload, context="backpack funding")
    amount = require_float(payload, "amount", "payment", "fundingPayment", "funding_payment", context="backpack funding")
    return (
        AccountEvent(
            id=require_string(payload, "id", "fundingId", "funding_id", context="backpack funding"),
            event_type=EventType.FUNDING_SETTLEMENT,
            origin=EventOrigin.SYSTEM,
            asset=require_string(payload, "asset", "currency", context="backpack funding"),
            amount=amount,
            pnl_effect=amount,
            position_effect=f"Funding settlement on {symbol}",
            occurred_at=require_timestamp(payload, "timestamp", "time", "settledAt", "settled_at", context="backpack funding"),
        ),
        [],
    )


def normalize_candle(payload: Mapping[str, Any]) -> tuple[Candle, list[str]]:
    return (
        Candle(
            timestamp=require_timestamp(payload, "timestamp", "time", "t", "start", "end", "startTime", "start_time", context="backpack kline"),
            open=require_float(payload, "open", "o", context="backpack kline"),
            high=require_float(payload, "high", "h", context="backpack kline"),
            low=require_float(payload, "low", "l", context="backpack kline"),
            close=require_float(payload, "close", "c", context="backpack kline"),
            volume=require_float(payload, "volume", "v", context="backpack kline"),
        ),
        [],
    )
