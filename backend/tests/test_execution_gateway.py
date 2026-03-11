from __future__ import annotations

import pytest

from app.infrastructure.gateways.execution_gateway import (
    BackpackExecutionGateway,
    _to_backpack_client_id,
    _to_backpack_side,
)
from app.infrastructure.state import RuntimeState


class MemoryState:
    pass


class StubBackpackClient:
    def __init__(self) -> None:
        self.payload = None

    async def get_market(self, symbol):  # noqa: ANN001
        return {
            "filters": {
                "quantity": {
                    "stepSize": "0.00001",
                    "minQuantity": "0.00001",
                }
            }
        }

    async def create_order(self, order):  # noqa: ANN001
        self.payload = order.to_payload()
        return {"orderId": "bp_123", "status": "Accepted"}


def test_side_mapping_normalizes_long_short() -> None:
    assert _to_backpack_side("long") == "Bid"
    assert _to_backpack_side("short") == "Ask"
    assert _to_backpack_side("Bid") == "Bid"
    assert _to_backpack_side("Ask") == "Ask"
    assert _to_backpack_side("long", reduce_only=True) == "Ask"
    assert _to_backpack_side("short", reduce_only=True) == "Bid"


def test_client_id_maps_to_uint32() -> None:
    value = _to_backpack_client_id("strat_001-abcdef123456")
    assert isinstance(value, int)
    assert 0 <= value <= 0xFFFFFFFF


@pytest.mark.asyncio
async def test_live_gateway_submits_bid_ask_and_uint32() -> None:
    state = MemoryState()
    client = StubBackpackClient()
    runtime_state = RuntimeState(state)
    runtime_state.set("backpack_client", client)
    gateway = BackpackExecutionGateway(runtime_state=runtime_state, mode="live")

    order = await gateway.submit_market_order(
        symbol="BTC_USDC_PERP",
        side="long",
        quantity=0.003,
        reduce_only=False,
        client_order_id="strat_001-abcdef123456",
    )

    assert client.payload is not None
    assert client.payload["side"] == "Bid"
    assert isinstance(client.payload["clientId"], int)
    assert client.payload["quantity"] == "0.003"
    assert order.exchange_order_id == "bp_123"
