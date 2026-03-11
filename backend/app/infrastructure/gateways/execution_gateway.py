from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_DOWN
from typing import Any
from uuid import uuid4
import zlib

from ...application.errors import ApplicationError, from_backpack_request_error
from ...application.ports.repositories import ExecutionGateway
from ...backpack import BackpackAuthError, BackpackOrderRequest, BackpackRequestError
from ...schema_read_models import ExecutionOrder
from ..state import RuntimeState


def _utc_now() -> str:
    return datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")


def _coerce_order_id(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("orderId", "order_id", "id"):
            value = payload.get(key)
            if value:
                return str(value)
        data = payload.get("data")
        if isinstance(data, dict):
            return _coerce_order_id(data)
        if isinstance(data, list) and data:
            return _coerce_order_id(data[0])
    if isinstance(payload, list) and payload:
        return _coerce_order_id(payload[0])
    return ""


def _coerce_status(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("status", "state"):
            value = payload.get(key)
            if value:
                return str(value).lower()
        data = payload.get("data")
        if isinstance(data, (dict, list)):
            return _coerce_status(data)
    if isinstance(payload, list) and payload:
        return _coerce_status(payload[0])
    return "submitted"


def _to_backpack_side(side: str, *, reduce_only: bool = False) -> str:
    normalized = side.strip().lower()
    if reduce_only:
        if normalized in {"long", "bid", "buy"}:
            return "Ask"
        if normalized in {"short", "ask", "sell"}:
            return "Bid"
    if normalized in {"long", "bid", "buy"}:
        return "Bid"
    if normalized in {"short", "ask", "sell"}:
        return "Ask"
    return side


def _to_backpack_client_id(client_order_id: str) -> int:
    # Backpack expects uint32 clientId; keep our internal string id and derive a stable transport id.
    return zlib.crc32(client_order_id.encode("utf-8")) & 0xFFFFFFFF


def _as_decimal_string(value: object, fallback: str) -> str:
    if value in (None, ""):
        return fallback
    return str(value)


def _normalize_quantity(quantity: float, *, step_size: str, min_quantity: str) -> float:
    step = Decimal(step_size)
    minimum = Decimal(min_quantity)
    raw = Decimal(str(quantity))
    normalized = raw.quantize(step, rounding=ROUND_DOWN)
    if normalized < minimum:
        normalized = minimum
    return float(normalized)


@dataclass(slots=True)
class BackpackExecutionGateway(ExecutionGateway):
    runtime_state: RuntimeState
    mode: str

    async def submit_market_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool,
        client_order_id: str,
    ) -> ExecutionOrder:
        submitted_at = _utc_now()
        strategy_placeholder = ""
        if self.mode != "live":
            return ExecutionOrder(
                id=f"ord_{uuid4().hex[:10]}",
                strategy_id="",
                strategy_name=strategy_placeholder,
                client_order_id=client_order_id,
                exchange_order_id=f"mock_{uuid4().hex[:10]}",
                symbol=symbol,
                side=side,
                action="close" if reduce_only else "open",
                status="filled",
                quantity=round(quantity, 6),
                price=0.0,
                reduce_only=reduce_only,
                submitted_at=submitted_at,
                updated_at=submitted_at,
            )

        client = self.runtime_state.get("backpack_client")
        if client is None:
            raise ApplicationError(
                code="execution_provider_not_initialized",
                message="Backpack live execution client is not initialized.",
                status_code=503,
                provider="backpack",
                retryable=True,
            )

        market_payload = await client.get_market(symbol)
        step_size = "0.00001"
        min_quantity = "0.00001"
        if isinstance(market_payload, dict):
            filters = market_payload.get("filters")
            if isinstance(filters, dict):
                quantity_filters = filters.get("quantity")
                if isinstance(quantity_filters, dict):
                    step_size = _as_decimal_string(quantity_filters.get("stepSize"), step_size)
                    min_quantity = _as_decimal_string(quantity_filters.get("minQuantity"), min_quantity)

        normalized_quantity = _normalize_quantity(quantity, step_size=step_size, min_quantity=min_quantity)
        order = BackpackOrderRequest(
            symbol=symbol,
            side=_to_backpack_side(side, reduce_only=reduce_only),
            order_type="Market",
            quantity=f"{normalized_quantity:.8f}".rstrip("0").rstrip("."),
            client_id=_to_backpack_client_id(client_order_id),
            reduce_only=reduce_only,
        )
        try:
            payload = await client.create_order(order)
        except BackpackAuthError as exc:
            raise ApplicationError(
                code="provider_auth_error",
                message=str(exc),
                status_code=503,
                provider="backpack",
            ) from exc
        except BackpackRequestError as exc:
            raise from_backpack_request_error(exc) from exc

        return ExecutionOrder(
            id=f"ord_{uuid4().hex[:10]}",
            strategy_id="",
            strategy_name=strategy_placeholder,
            client_order_id=client_order_id,
            exchange_order_id=_coerce_order_id(payload),
            symbol=symbol,
            side=side,
            action="close" if reduce_only else "open",
            status=_coerce_status(payload),
            quantity=round(normalized_quantity, 8),
            price=0.0,
            reduce_only=reduce_only,
            submitted_at=submitted_at,
            updated_at=_utc_now(),
        )
