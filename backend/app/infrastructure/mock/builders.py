from __future__ import annotations

import math

from ...schemas import BacktestRunAccepted, Candle, EquityPoint, PriceSource, TradeMarker
from .fixtures import CANDLES


def build_backtest_acceptance(
    *,
    backtest_id: str,
    strategy_id: str,
    strategy_kind: str,
    created_at: str,
    demo_mode: bool,
) -> BacktestRunAccepted:
    return BacktestRunAccepted(
        id=backtest_id,
        strategy_id=strategy_id,
        strategy_kind=strategy_kind,
        status="completed",
        created_at=created_at,
        result_path=f"/api/backtests/{backtest_id}",
        poll_after_ms=0,
        demo_mode=demo_mode,
    )


def generate_candles(*, symbol: str, seed: int, request) -> list[Candle]:
    symbol_base = {
        "BTC_USDC_PERP": 62000.0,
        "ETH_USDC_PERP": 3200.0,
        "SOL_USDC_PERP": 170.0,
        "DOGE_USDC_PERP": 0.21,
        "BNB_USDC_PERP": 590.0,
    }.get(symbol, 100.0)
    price_source = str(request.price_source)
    price_bias = {
        PriceSource.LAST: 1.0,
        PriceSource.MARK: 0.998,
        PriceSource.INDEX: 0.996,
        "last": 1.0,
        "mark": 0.998,
        "index": 0.996,
    }[price_source]
    base = symbol_base * price_bias * (1 + ((seed % 7) - 3) * 0.012)
    amplitude = max(base * 0.012, 0.015)
    candles: list[Candle] = []
    previous_close = base

    for index, template in enumerate(CANDLES):
        drift = math.sin((seed % 11) + index * 0.72) * amplitude
        impulse = math.cos((seed % 17) + index * 0.41) * amplitude * 0.46
        open_price = previous_close
        close_price = max(0.0001, open_price + drift + impulse)
        high = max(open_price, close_price) + abs(amplitude * 0.45 * math.cos(index + seed))
        low = min(open_price, close_price) - abs(amplitude * 0.35 * math.sin(index + seed / 3))
        volume = template.volume + (seed % 200) + index * 35
        candles.append(
            Candle(
                timestamp=template.timestamp,
                open=round(open_price, 4),
                high=round(high, 4),
                low=round(max(0.0001, low), 4),
                close=round(close_price, 4),
                volume=round(volume, 2),
            )
        )
        previous_close = close_price

    return candles


def generate_trade_markers(
    *,
    strategy_id: str,
    strategy_kind: str,
    candles: list[Candle],
    seed: int,
) -> list[TradeMarker]:
    if len(candles) < 4:
        return []

    side = "short" if strategy_kind == "script" or seed % 2 else "long"
    return [
        TradeMarker(id=f"{strategy_id}-open-1", timestamp=candles[1].timestamp, type="open", side=side, price=candles[1].close, reason="Signal confirmed after volatility filter"),
        TradeMarker(id=f"{strategy_id}-close-1", timestamp=candles[3].timestamp, type="close", side=side, price=candles[3].close, reason="Exit on momentum fade and risk budget reclaim"),
        TradeMarker(id=f"{strategy_id}-open-2", timestamp=candles[4].timestamp, type="open", side=side, price=candles[4].open, reason="Re-entry after regime reset"),
        TradeMarker(id=f"{strategy_id}-close-2", timestamp=candles[-1].timestamp, type="close", side=side, price=candles[-1].close, reason="Flat by session close"),
    ]


def generate_equity_curve(*, candles: list[Candle], seed: int) -> list[EquityPoint]:
    equity = 100.0
    points: list[EquityPoint] = []
    divisor = max(abs(candles[0].open), 1.0)

    for index, candle in enumerate(candles):
        step_return = ((candle.close - candle.open) / divisor) * (35 + (seed % 13))
        step_return += math.sin(seed + index) * 0.35
        equity = round(equity + step_return, 2)
        points.append(EquityPoint(timestamp=candle.timestamp, equity=equity))

    return points
