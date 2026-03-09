from __future__ import annotations

from pydantic import Field

from .domain.shared.enums import EventOrigin, EventType, PriceSource
from .schema_core import APIModel


class ProfileSummary(APIModel):
    total_equity: float
    available_margin: float
    unrealized_pnl: float
    realized_pnl_24h: float
    win_rate: float
    risk_level: str
    price_source: PriceSource
    synced_at: str


class AssetBalance(APIModel):
    asset: str
    available: float
    locked: float
    collateral_value: float
    portfolio_weight: float
    change_24h: float
    price_source: PriceSource = PriceSource.MARK


class Position(APIModel):
    symbol: str
    side: str
    quantity: float
    entry_price: float
    mark_price: float
    liquidation_price: float | None
    unrealized_pnl: float
    margin_used: float
    opened_at: str
    price_source: PriceSource
    exchange_extra: dict[str, str | float | int | None] = Field(default_factory=dict)


class AccountEvent(APIModel):
    id: str
    event_type: EventType
    origin: EventOrigin
    asset: str
    amount: float
    pnl_effect: float
    position_effect: str
    occurred_at: str


class StrategySummary(APIModel):
    id: str
    name: str
    kind: str
    description: str = ""
    market: str
    account_id: str = ""
    runtime: str
    status: str
    last_backtest: str
    sharpe: float
    price_source: PriceSource
    parameters: dict[str, str | float | int | bool] = Field(default_factory=dict)


class Candle(APIModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class TradeMarker(APIModel):
    id: str
    timestamp: str
    candle_timestamp: str = ""
    action: str = ""
    type: str
    side: str
    price: float
    qty: float = 0.0
    reason: str
    related_trade_id: str = ""
    related_order_id: str = ""


class EquityPoint(APIModel):
    timestamp: str
    equity: float


class BacktestResult(APIModel):
    id: str
    strategy_id: str = ""
    strategy_kind: str = "template"
    strategy_name: str
    exchange_id: str = ""
    market_type: str = ""
    symbol: str = ""
    interval: str = ""
    start_time: int = 0
    end_time: int = 0
    price_source: PriceSource
    chart_price_source: PriceSource = PriceSource.MARK
    fee_bps: float = 0
    slippage_bps: float = 0
    status: str = "completed"
    created_at: str = ""
    completed_at: str = ""
    total_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    candles: list[Candle]
    trade_markers: list[TradeMarker]
    equity_curve: list[EquityPoint]
    chart_warnings: list[str] = Field(default_factory=list)


class MarketMetric(APIModel):
    label: str
    value: str
    freshness: str
    tone: str = "neutral"


class ExchangeAccount(APIModel):
    id: str
    exchange: str
    label: str
    market_type: str
    last_credential_rotation: str
    status: str


class AlertEvent(APIModel):
    id: str
    level: str
    title: str
    detail: str
    occurred_at: str
