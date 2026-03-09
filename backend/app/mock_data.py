from __future__ import annotations

from .infrastructure.mock.builders import (
    build_backtest_acceptance,
    generate_candles,
    generate_equity_curve,
    generate_trade_markers,
)
from .infrastructure.mock.fixtures import (
    ACCOUNT_EVENTS,
    ALERTS,
    ASSET_BALANCES,
    BACKTEST_RESULT,
    CANDLES,
    EXCHANGE_ACCOUNTS,
    MARKET_PULSE,
    MARKET_SYMBOLS,
    POSITIONS,
    PROFILE_SUMMARY,
    RISK_CONTROLS,
    STRATEGIES,
)

# Compatibility exports for the existing app/tests surface.
_generate_candles = generate_candles
_generate_trade_markers = generate_trade_markers
_generate_equity_curve = generate_equity_curve

__all__ = [
    "PROFILE_SUMMARY",
    "ASSET_BALANCES",
    "POSITIONS",
    "ACCOUNT_EVENTS",
    "STRATEGIES",
    "CANDLES",
    "BACKTEST_RESULT",
    "MARKET_PULSE",
    "EXCHANGE_ACCOUNTS",
    "MARKET_SYMBOLS",
    "RISK_CONTROLS",
    "ALERTS",
    "build_backtest_acceptance",
    "_generate_candles",
    "_generate_trade_markers",
    "_generate_equity_curve",
]
