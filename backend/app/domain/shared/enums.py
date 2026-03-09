from __future__ import annotations

from enum import Enum


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
