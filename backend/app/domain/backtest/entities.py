from __future__ import annotations

from dataclasses import dataclass, field

from ..shared.enums import PriceSource


@dataclass(slots=True)
class PriceBar:
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class BacktestSpec:
    symbol: str
    interval: str
    start_time: int
    end_time: int
    price_source: PriceSource
    fee_bps: float
    slippage_bps: float


@dataclass(slots=True)
class RiskEnvelope:
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


@dataclass(slots=True)
class StrategySnapshot:
    id: str
    name: str
    kind: str


@dataclass(slots=True)
class TradeEvent:
    action: str
    side: str
    candle_timestamp: str
    timestamp: str
    price: float
    qty: float
    reason: str
    related_trade_id: str
    related_order_id: str


@dataclass(slots=True)
class EquitySample:
    timestamp: str
    equity: float


@dataclass(slots=True)
class SimulationStats:
    total_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float


@dataclass(slots=True)
class BacktestSimulation:
    candles: list[PriceBar]
    trades: list[TradeEvent]
    equity_curve: list[EquitySample]
    stats: SimulationStats
    warnings: list[str] = field(default_factory=list)
