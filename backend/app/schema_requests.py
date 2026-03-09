from __future__ import annotations

from pydantic import Field

from .domain.shared.enums import PriceSource
from .schema_core import APIModel
from .schema_read_models import Candle


class KlineQuery(APIModel):
    symbol: str
    interval: str
    start_time: int
    end_time: int
    price_source: PriceSource


class KlineResponse(APIModel):
    symbol: str
    interval: str
    start_time: int
    end_time: int
    price_source: PriceSource
    candles: list[Candle]


class BacktestRequest(APIModel):
    symbol: str
    interval: str
    start_time: int
    end_time: int
    price_source: PriceSource
    fee_bps: float
    slippage_bps: float


class StrategyUpsertRequest(APIModel):
    name: str
    kind: str
    description: str = ""
    market: str
    account_id: str = ""
    runtime: str
    status: str
    price_source: PriceSource
    parameters: dict[str, str | float | int | bool] = Field(default_factory=dict)


class RiskControls(APIModel):
    max_open_positions: int
    max_consecutive_loss: int
    max_symbol_exposure: float
    stop_loss_percent: float
    max_trade_risk: float
    max_slippage_percent: float
    max_spread_percent: float
    volatility_filter_percent: float
    max_position_notional: float
    daily_loss_limit: float
    max_leverage: float
    allowed_symbols: list[str]
    trading_window_start: str
    trading_window_end: str
    kill_switch_enabled: bool
    require_mark_price: bool
    updated_at: str


class BacktestRunAccepted(APIModel):
    id: str
    strategy_id: str
    strategy_kind: str
    status: str
    created_at: str
    result_path: str
    poll_after_ms: int = 0
    demo_mode: bool = False
