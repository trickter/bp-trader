from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import math
from statistics import mean, pstdev

from .entities import (
    BacktestSimulation,
    BacktestSpec,
    EquitySample,
    PriceBar,
    RiskEnvelope,
    SimulationStats,
    StrategySnapshot,
    TradeEvent,
)


INTERVAL_SECONDS = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


@dataclass(slots=True)
class PositionState:
    side: str
    avg_entry: float = 0.0
    qty: float = 0.0
    open_slots: int = 0
    cycle_pnl: float = 0.0
    entry_index: int | None = None

    @property
    def is_open(self) -> bool:
        return self.qty > 0


def simulate_backtest(
    *,
    strategy: StrategySnapshot,
    spec: BacktestSpec,
    risk: RiskEnvelope,
    candles: list[PriceBar],
) -> BacktestSimulation:
    starting_equity = _infer_account_equity(risk)
    trades, warnings = _simulate_trades(strategy=strategy, spec=spec, risk=risk, candles=candles)
    equity_curve = _build_equity_curve(candles=candles, trades=trades, starting_equity=starting_equity)
    total_return = round(((equity_curve[-1].equity - starting_equity) / starting_equity) * 100, 2) if equity_curve else 0.0
    stats = SimulationStats(
        total_return=total_return,
        max_drawdown=_calculate_max_drawdown(equity_curve),
        sharpe=_calculate_sharpe(equity_curve),
        win_rate=_calculate_win_rate(trades),
    )
    price_source = str(spec.price_source)
    warnings.extend(
        _build_chart_warnings(
            candles=candles,
            trades=trades,
            backtest_price_source=price_source,
            chart_price_source=price_source,
        )
    )
    return BacktestSimulation(
        candles=candles,
        trades=trades,
        equity_curve=equity_curve,
        stats=stats,
        warnings=warnings,
    )


def _simulate_trades(
    *,
    strategy: StrategySnapshot,
    spec: BacktestSpec,
    risk: RiskEnvelope,
    candles: list[PriceBar],
) -> tuple[list[TradeEvent], list[str]]:
    if len(candles) < 3:
        return [], []

    warnings: list[str] = []
    if spec.symbol not in risk.allowed_symbols:
        return [], [f"Symbol {spec.symbol} is outside the allowed risk universe."]

    side = "short" if strategy.kind == "script" else "long"
    trades: list[TradeEvent] = []
    interval_seconds = INTERVAL_SECONDS.get(spec.interval, 3600)
    position = PositionState(side=side)
    rolling_signal = 0
    consecutive_losses = 0
    daily_losses: dict[str, float] = {}
    warned_limits: set[str] = set()

    max_position_notional = max(min(risk.max_position_notional, risk.max_symbol_exposure), 0.0)
    max_open_positions = max(risk.max_open_positions, 1)
    stop_loss_fraction = max(risk.stop_loss_percent, 0.0) / 100 or 0.10
    max_trade_risk = max(risk.max_trade_risk, 0.0)
    max_slippage_fraction = max(risk.max_slippage_percent, 0.0) / 100
    max_spread_percent = max(risk.max_spread_percent, 0.0)
    volatility_filter_percent = max(risk.volatility_filter_percent, 0.0)

    def append_warning(message: str) -> None:
        if message not in warned_limits:
            warnings.append(message)
            warned_limits.add(message)

    def in_trading_window(candle: PriceBar) -> bool:
        candle_dt = datetime.fromisoformat(candle.timestamp.replace("Z", "+00:00"))
        hhmm = candle_dt.strftime("%H:%M")
        start = risk.trading_window_start
        end = risk.trading_window_end
        if start <= end:
            return start <= hhmm <= end
        return hhmm >= start or hhmm <= end

    def candle_range_percent(candle: PriceBar) -> float:
        return abs(candle.high - candle.low) / max(abs(candle.open), 1.0) * 100

    def candle_spread_proxy_percent(candle: PriceBar) -> float:
        return max(abs(candle.close - candle.open) / max(abs(candle.open), 1.0) * 100, 0.01)

    def available_notional() -> float:
        used = position.qty * position.avg_entry if position.qty > 0 else 0.0
        return max(max_position_notional - used, 0.0)

    def compute_entry_qty(price: float) -> float:
        inferred_qty = _infer_qty(symbol=spec.symbol)
        slot_cap = max_position_notional / max_open_positions if max_open_positions else max_position_notional
        qty_by_slot = slot_cap / max(price, 1.0)
        qty_by_notional = available_notional() / max(price, 1.0)
        qty_by_risk = max_trade_risk / max(price * stop_loss_fraction, 1e-9) if max_trade_risk > 0 else inferred_qty
        return round(max(min(inferred_qty, qty_by_slot, qty_by_notional, qty_by_risk), 0.0), 6)

    def fill_price(price: float, side_value: str, opening: bool) -> float:
        direction = 1 if side_value == "long" else -1
        multiplier = 1 + (max_slippage_fraction * direction if opening else -max_slippage_fraction * direction)
        return round(price * multiplier, 6)

    def register_loss(candle: PriceBar, pnl_value: float) -> None:
        if pnl_value >= 0:
            return
        key = candle.timestamp[:10]
        daily_losses[key] = daily_losses.get(key, 0.0) + abs(pnl_value)

    def close_position(*, candle: PriceBar, action: str, price: float, reason: str, offset_seconds: int) -> None:
        nonlocal consecutive_losses, rolling_signal
        if position.qty <= 0:
            return
        trades.append(
            _trade_for_candle(
                candle=candle,
                action=action,
                side=side,
                qty=round(position.qty, 6),
                price=price,
                reason=reason,
                index=len(trades) + 1,
                offset_seconds=offset_seconds,
            )
        )
        direction = 1 if side == "long" else -1
        pnl_value = (price - position.avg_entry) * direction * position.qty
        position.cycle_pnl += pnl_value
        register_loss(candle, pnl_value)
        consecutive_losses = consecutive_losses + 1 if position.cycle_pnl < 0 else 0
        position.avg_entry = 0.0
        position.qty = 0.0
        position.open_slots = 0
        position.cycle_pnl = 0.0
        position.entry_index = None
        rolling_signal = 0

    for index in range(1, len(candles)):
        previous = candles[index - 1]
        candle = candles[index]
        daily_loss = daily_losses.get(candle.timestamp[:10], 0.0)
        momentum = (candle.close - previous.close) / max(abs(previous.close), 1.0)
        rolling_signal += 1 if momentum > 0 else -1
        rolling_signal = max(-3, min(3, rolling_signal))

        if side == "long":
            should_open = momentum > 0.0012 or rolling_signal >= 2
            should_add = momentum > 0.0022
            should_reverse = momentum < -0.0014 or rolling_signal <= -2
        else:
            should_open = momentum < -0.0012 or rolling_signal <= -2
            should_add = momentum < -0.0022
            should_reverse = momentum > 0.0014 or rolling_signal >= 2

        tradable_now = in_trading_window(candle)
        market_filtered = (
            candle_range_percent(candle) > volatility_filter_percent
            or candle_spread_proxy_percent(candle) > max_spread_percent
        )

        if not position.is_open:
            if consecutive_losses >= risk.max_consecutive_loss:
                append_warning(f"Trading halted after {risk.max_consecutive_loss} consecutive losing cycles.")
                continue
            if daily_loss >= risk.daily_loss_limit:
                append_warning(f"Daily loss limit reached on {candle.timestamp[:10]}.")
                continue
            if not tradable_now:
                continue
            if market_filtered:
                append_warning(
                    f"Market filter blocked entries when spread proxy exceeded {risk.max_spread_percent}% or volatility exceeded {risk.volatility_filter_percent}%."
                )
                continue
            cycle_gate = index % 3 == 0
            if should_open or cycle_gate:
                qty = compute_entry_qty(candle.open)
                if qty <= 0:
                    append_warning("Risk envelope reduced position size to zero.")
                    continue
                entry_price = fill_price(candle.open, side, True)
                trades.append(
                    _trade_for_candle(
                        candle=candle,
                        action="open",
                        side=side,
                        qty=qty,
                        price=entry_price,
                        reason="Signal crossed entry threshold within account and trade risk limits",
                        index=len(trades) + 1,
                        offset_seconds=max(interval_seconds // 4, 1),
                    )
                )
                position.open_slots = 1
                position.qty = qty
                position.avg_entry = entry_price
                position.entry_index = index
                position.cycle_pnl = 0.0
                rolling_signal = 0
            continue

        holding_period = index - (position.entry_index or index)
        stop_price = position.avg_entry * (1 - stop_loss_fraction) if side == "long" else position.avg_entry * (1 + stop_loss_fraction)
        stop_triggered = candle.low <= stop_price if side == "long" else candle.high >= stop_price
        if stop_triggered:
            close_position(
                candle=candle,
                action="stop",
                price=round(stop_price, 6),
                reason=f"Stop loss hit at {risk.stop_loss_percent:.1f}%",
                offset_seconds=max(interval_seconds // 2, 1),
            )
            continue

        can_add = (
            tradable_now
            and not market_filtered
            and position.open_slots < max_open_positions
            and holding_period >= 1
            and should_add
            and daily_loss < risk.daily_loss_limit
        )
        if can_add:
            add_qty = compute_entry_qty((candle.open + candle.close) / 2)
            if add_qty > 0:
                add_price = fill_price((candle.open + candle.close) / 2, side, True)
                trades.append(
                    _trade_for_candle(
                        candle=candle,
                        action="add",
                        side=side,
                        qty=add_qty,
                        price=add_price,
                        reason="Position scaled while respecting symbol exposure and trade risk",
                        index=len(trades) + 1,
                        offset_seconds=max(interval_seconds // 3, 1),
                    )
                )
                new_qty = position.qty + add_qty
                position.avg_entry = ((position.avg_entry * position.qty) + (add_price * add_qty)) / max(new_qty, 1e-9)
                position.qty = new_qty
                position.open_slots += 1
                continue

        should_reduce = holding_period >= 2 and position.open_slots > 1 and (should_reverse or holding_period >= 3)
        if should_reduce:
            reduce_qty = round(min(position.qty / max(position.open_slots, 1), position.qty * 0.5), 6)
            reduce_price = fill_price((candle.high + candle.low) / 2, side, False)
            trades.append(
                _trade_for_candle(
                    candle=candle,
                    action="reduce",
                    side=side,
                    qty=reduce_qty,
                    price=reduce_price,
                    reason="Risk budget cut after signal decay",
                    index=len(trades) + 1,
                    offset_seconds=max(interval_seconds // 2, 1),
                )
            )
            direction = 1 if side == "long" else -1
            pnl_value = (reduce_price - position.avg_entry) * direction * reduce_qty
            position.cycle_pnl += pnl_value
            register_loss(candle, pnl_value)
            position.qty = max(position.qty - reduce_qty, 0.0)
            position.open_slots = max(position.open_slots - 1, 1 if position.qty > 0 else 0)
            continue

        should_close = (
            should_reverse
            or holding_period >= 5
            or index == len(candles) - 1
            or (holding_period >= 2 and index % 4 == 0)
        )
        if should_close:
            close_position(
                candle=candle,
                action="close",
                price=fill_price(candle.close, side, False),
                reason="Exit rule reached on this bar",
                offset_seconds=max(interval_seconds - 1, 1),
            )

    if position.is_open and trades and trades[-1].action not in {"close", "stop"}:
        last_candle = candles[-1]
        close_position(
            candle=last_candle,
            action="close",
            price=fill_price(last_candle.close, side, False),
            reason="Forced flat at backtest window end",
            offset_seconds=max(interval_seconds - 1, 1),
        )

    return trades, warnings


def _trade_for_candle(
    *,
    candle: PriceBar,
    action: str,
    side: str,
    qty: float,
    price: float,
    reason: str,
    index: int,
    offset_seconds: int,
) -> TradeEvent:
    candle_dt = datetime.fromisoformat(candle.timestamp.replace("Z", "+00:00"))
    trade_timestamp = candle_dt.timestamp() + offset_seconds
    trade_dt = datetime.fromtimestamp(trade_timestamp, tz=UTC).isoformat().replace("+00:00", "Z")
    return TradeEvent(
        action=action,
        side=side,
        candle_timestamp=candle.timestamp,
        timestamp=trade_dt,
        price=round(price, 6),
        qty=qty,
        reason=reason,
        related_trade_id=f"trade_{index:03d}",
        related_order_id=f"order_{index:03d}",
    )


def _build_equity_curve(*, candles: list[PriceBar], trades: list[TradeEvent], starting_equity: float) -> list[EquitySample]:
    if not candles:
        return []

    trade_index_by_candle: dict[str, list[TradeEvent]] = {}
    for trade in trades:
        trade_index_by_candle.setdefault(trade.candle_timestamp, []).append(trade)

    equity = starting_equity
    position_side: str | None = None
    avg_entry = 0.0
    position_qty = 0.0
    closed_pnl = 0.0
    points: list[EquitySample] = []

    for candle in candles:
        for trade in trade_index_by_candle.get(candle.timestamp, []):
            if trade.action in {"open", "add"}:
                new_qty = position_qty + trade.qty
                avg_entry = ((avg_entry * position_qty) + (trade.price * trade.qty)) / new_qty if new_qty > 0 else trade.price
                position_qty = new_qty
                position_side = trade.side
            elif trade.action in {"reduce", "close", "stop"} and position_side:
                close_qty = min(position_qty, trade.qty)
                direction = 1 if position_side == "long" else -1
                closed_pnl += (trade.price - avg_entry) * direction * close_qty
                position_qty = max(position_qty - close_qty, 0.0)
                if position_qty == 0:
                    avg_entry = 0.0
                    position_side = None

        unrealized = 0.0
        if position_side and position_qty > 0:
            direction = 1 if position_side == "long" else -1
            unrealized = (candle.close - avg_entry) * direction * position_qty

        equity = round(starting_equity + closed_pnl + unrealized, 2)
        points.append(EquitySample(timestamp=candle.timestamp, equity=equity))

    return points


def _calculate_max_drawdown(points: list[EquitySample]) -> float:
    if not points:
        return 0.0
    peak = points[0].equity
    drawdown = 0.0
    for point in points:
        peak = max(peak, point.equity)
        drawdown = min(drawdown, ((point.equity - peak) / max(peak, 1.0)) * 100)
    return round(drawdown, 2)


def _calculate_sharpe(points: list[EquitySample]) -> float:
    if len(points) < 2:
        return 0.0
    returns = []
    previous = points[0].equity
    for point in points[1:]:
        returns.append((point.equity - previous) / max(abs(previous), 1.0))
        previous = point.equity
    volatility = pstdev(returns) if len(returns) > 1 else 0.0
    if volatility == 0:
        return 0.0
    return round((mean(returns) / volatility) * math.sqrt(len(returns)), 2)


def _calculate_win_rate(trades: list[TradeEvent]) -> float:
    entries = [trade for trade in trades if trade.action in {"open", "add"}]
    exits = [trade for trade in trades if trade.action in {"reduce", "close", "stop"}]
    if not entries or not exits:
        return 0.0
    wins = 0
    comparisons = min(len(entries), len(exits))
    for index in range(comparisons):
        wins += 1 if exits[index].price >= entries[index].price else 0
    return round((wins / comparisons) * 100, 1)


def _build_chart_warnings(
    *,
    candles: list[PriceBar],
    trades: list[TradeEvent],
    backtest_price_source: str,
    chart_price_source: str,
) -> list[str]:
    warnings: list[str] = []
    if backtest_price_source != chart_price_source:
        warnings.append("Backtest price source and chart price source do not match.")
    candle_times = {candle.timestamp for candle in candles}
    if candles:
        min_price = min(candle.low for candle in candles)
        max_price = max(candle.high for candle in candles)
        for trade in trades:
            if trade.candle_timestamp not in candle_times:
                warnings.append(f"Trade marker {trade.related_trade_id} falls outside the candle range.")
            if trade.price < min_price or trade.price > max_price:
                warnings.append(f"Trade marker {trade.related_trade_id} price falls outside the candle price range.")
    return warnings


def _infer_account_equity(risk: RiskEnvelope) -> float:
    return max(risk.max_position_notional / max(risk.max_leverage, 1.0), 100.0)


def _infer_qty(*, symbol: str) -> float:
    if symbol.startswith("BTC"):
        return 0.25
    if symbol.startswith("ETH"):
        return 2.0
    if symbol.startswith("SOL"):
        return 35.0
    return 100.0
