from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class BackpackAuthConfig:
    base_url: str = "https://api.backpack.exchange"
    api_key: str | None = None
    private_key: str | bytes | None = None
    window_ms: int = 5_000
    timeout_seconds: float = 10.0
    user_agent: str = "backpack-quant-console/0.1.0"


@dataclass(slots=True, frozen=True)
class BackpackRequestConfig:
    instruction: str
    path: str
    method: str = "GET"


@dataclass(slots=True, frozen=True)
class BackpackOrderRequest:
    symbol: str
    side: str
    order_type: str
    quantity: str
    client_id: int | None = None
    reduce_only: bool | None = None
    time_in_force: str | None = None
    post_only: bool | None = None
    price: str | None = None
    trigger_price: str | None = None

    def to_payload(self) -> dict[str, object | None]:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "orderType": self.order_type,
            "quantity": self.quantity,
            "clientId": self.client_id,
            "reduceOnly": self.reduce_only,
            "timeInForce": self.time_in_force,
            "postOnly": self.post_only,
            "price": self.price,
            "triggerPrice": self.trigger_price,
        }
