from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Mapping

from ..domain.shared.enums import EventOrigin, EventType
from .base import ProviderError


def unwrap_object(payload: Any, *, context: str = "payload") -> Mapping[str, Any]:
    if isinstance(payload, Mapping):
        for key in ("data", "result"):
            nested = payload.get(key)
            if isinstance(nested, Mapping):
                return nested
            if isinstance(nested, list):
                return coerce_single_mapping(nested, context=f"{context}.{key}")
        return payload
    if isinstance(payload, list):
        return coerce_single_mapping(payload, context=context)
    raise ProviderError(f"{context} expected an object payload")


def pick_latest_object(payload: Any, *, context: str) -> Mapping[str, Any]:
    if isinstance(payload, list):
        return coerce_single_mapping(payload[:1], context=context)
    if isinstance(payload, Mapping):
        nested = payload.get("data")
        if isinstance(nested, list):
            return coerce_single_mapping(nested[:1], context=f"{context}.data")
    return unwrap_object(payload, context=context)


def unwrap_list(payload: Any, *, context: str = "payload") -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return coerce_mapping_list(payload, context=context)
    if isinstance(payload, Mapping):
        for key in ("items", "rows", "results", "data", "result"):
            nested = payload.get(key)
            if isinstance(nested, list):
                return coerce_mapping_list(nested, context=f"{context}.{key}")
            if nested is not None:
                raise ProviderError(f"{context}.{key} expected a list payload")
        raise ProviderError(f"{context} expected a list container")
    raise ProviderError(f"{context} expected a list payload")


def coerce_single_mapping(payload: list[Any], *, context: str) -> Mapping[str, Any]:
    items = coerce_mapping_list(payload, context=context)
    if len(items) != 1:
        raise ProviderError(f"{context} expected a single object but received {len(items)} items")
    return items[0]


def coerce_mapping_list(payload: list[Any], *, context: str) -> list[Mapping[str, Any]]:
    invalid_items = [index for index, item in enumerate(payload) if not isinstance(item, Mapping)]
    if invalid_items:
        joined = ", ".join(str(index) for index in invalid_items[:3])
        raise ProviderError(f"{context} contained non-object entries at indexes {joined}")
    return list(payload)


def pick(payload: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def floatify(value: Any) -> float:
    if value in (None, "", False):
        return 0.0
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def float_or_none(value: Any) -> float | None:
    if value in (None, "", False):
        return None
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stringify(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def stringify_number(value: Any, fallback: str = "") -> str:
    if value in (None, ""):
        return fallback
    if isinstance(value, (int, float)):
        return str(value)
    return stringify(value, fallback=fallback)


def format_rate_percent(value: float) -> str:
    return f"{value * 100:+.3f}%"


def normalize_symbol(payload: Mapping[str, Any]) -> str:
    return stringify(
        pick(payload, "symbol", "market", "product", "productId", "instrument", "name"),
        fallback="UNKNOWN",
    )


def require_symbol(payload: Mapping[str, Any], *, context: str) -> str:
    symbol = normalize_symbol(payload)
    if symbol == "UNKNOWN":
        raise ProviderError(f"{context} missing required field: symbol/market/product")
    return symbol


def require_string(payload: Mapping[str, Any], *keys: str, context: str) -> str:
    value = pick(payload, *keys)
    if value is None or not stringify(value):
        raise ProviderError(f"{context} missing required field: {'/'.join(keys)}")
    return stringify(value)


def require_float(payload: Mapping[str, Any], *keys: str, context: str) -> float:
    number = float_or_none(pick(payload, *keys))
    if number is None:
        raise ProviderError(f"{context} missing required numeric field: {'/'.join(keys)}")
    return number


def require_timestamp(payload: Mapping[str, Any], *keys: str, context: str) -> str:
    timestamp = coerce_timestamp(pick(payload, *keys))
    if timestamp is None:
        raise ProviderError(f"{context} missing required timestamp field: {'/'.join(keys)}")
    return timestamp


def infer_side(payload: Mapping[str, Any], quantity: float) -> str:
    raw_side = stringify(pick(payload, "side"), fallback="").lower()
    if raw_side in {"long", "short"}:
        return raw_side
    signed_qty = floatify(pick(payload, "netQuantity", "net_quantity", "quantity", "qty", "size"))
    if signed_qty < 0:
        return "short"
    if signed_qty > 0:
        return "long"
    return "long" if quantity >= 0 else "short"


def coerce_timestamp(value: Any) -> str | None:
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
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
            except ValueError:
                return None
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


def sum_values(rows: list[Mapping[str, Any]], keys: tuple[str, ...]) -> float:
    total = 0.0
    for row in rows:
        total += floatify(pick(row, *keys))
    return total


def map_event_type(raw_type: str) -> EventType:
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
    if "trade" in normalized or "fill" in normalized:
        return EventType.TRADE_FILL
    raise ProviderError(f"backpack fill has unsupported event type: {raw_type}")


def map_origin(raw_origin: str) -> EventOrigin:
    normalized = raw_origin.lower()
    if "strategy" in normalized or "algo" in normalized:
        return EventOrigin.STRATEGY
    if "manual" in normalized or "user" in normalized:
        return EventOrigin.MANUAL
    if "risk" in normalized or "liquid" in normalized or "adl" in normalized:
        return EventOrigin.RISK
    return EventOrigin.SYSTEM


def describe_position_effect(payload: Mapping[str, Any], fallback: str) -> str:
    symbol = normalize_symbol(payload)
    side = stringify(pick(payload, "side"), fallback="").lower()
    quantity = stringify_number(pick(payload, "quantity", "qty", "size"), fallback="")
    if symbol != "UNKNOWN" and quantity:
        descriptor = f"{side} {quantity}".strip()
        return f"{fallback} on {symbol} {descriptor}".strip()
    if symbol != "UNKNOWN":
        return f"{fallback} on {symbol}"
    return fallback


def infer_risk_level(total_equity: float, margin: float) -> str:
    if total_equity <= 0:
        return "unknown"
    usage = 1 - (margin / total_equity if total_equity else 0)
    if usage >= 0.75:
        return "elevated"
    if usage >= 0.45:
        return "managed"
    return "disciplined"
