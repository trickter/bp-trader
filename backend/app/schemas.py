from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class APIModel(BaseModel):
    model_config = ConfigDict(
      alias_generator=to_camel,
      populate_by_name=True,
      use_enum_values=True,
    )


class PriceSource(str, Enum):
    LAST = "last"
    MARK = "mark"
    INDEX = "index"


class EventType(str, Enum):
    TRADE_FILL = "trade_fill"
    FUNDING_SETTLEMENT = "funding_settlement"
    FEE_CHARGE = "fee_charge"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    LIQUIDATION = "liquidation"
    ADL = "adl"
    COLLATERAL_CONVERSION = "collateral_conversion"
    MANUAL_ADJUSTMENT = "manual_adjustment"


class EventOrigin(str, Enum):
    STRATEGY = "strategy"
    MANUAL = "manual"
    SYSTEM = "system"
    RISK = "risk"


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
    market: str
    runtime: str
    status: str
    last_backtest: str
    sharpe: float
    price_source: PriceSource


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
    type: str
    side: str
    price: float
    reason: str


class EquityPoint(APIModel):
    timestamp: str
    equity: float


class BacktestResult(APIModel):
    id: str
    strategy_name: str
    price_source: PriceSource
    total_return: float
    max_drawdown: float
    sharpe: float
    win_rate: float
    candles: list[Candle]
    trade_markers: list[TradeMarker]
    equity_curve: list[EquityPoint]


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
