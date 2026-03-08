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
