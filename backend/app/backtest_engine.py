from __future__ import annotations

from datetime import UTC, datetime

from .domain.backtest.entities import BacktestSpec, PriceBar, RiskEnvelope, StrategySnapshot
from .domain.backtest.service import simulate_backtest
from .schemas import BacktestRequest, BacktestResult, Candle, EquityPoint, RiskControls, StrategySummary, TradeMarker


def build_backtest_result(
    *,
    backtest_id: str,
    strategy: StrategySummary,
    request: BacktestRequest,
    risk_controls: RiskControls,
    candles: list[Candle],
    created_at: str,
    exchange_id: str,
    market_type: str,
) -> BacktestResult:
    simulation = simulate_backtest(
        strategy=StrategySnapshot(id=strategy.id, name=strategy.name, kind=strategy.kind),
        spec=BacktestSpec(
            symbol=request.symbol,
            interval=request.interval,
            start_time=request.start_time,
            end_time=request.end_time,
            price_source=request.price_source,
            fee_bps=request.fee_bps,
            slippage_bps=request.slippage_bps,
        ),
        risk=_to_risk_envelope(risk_controls),
        candles=[_to_price_bar(item) for item in candles],
    )
    return BacktestResult(
        id=backtest_id,
        strategy_id=strategy.id,
        strategy_kind=strategy.kind,
        strategy_name=strategy.name,
        exchange_id=exchange_id,
        market_type=market_type,
        symbol=request.symbol,
        interval=request.interval,
        start_time=request.start_time,
        end_time=request.end_time,
        price_source=request.price_source,
        chart_price_source=request.price_source,
        fee_bps=request.fee_bps,
        slippage_bps=request.slippage_bps,
        status="completed",
        created_at=created_at,
        completed_at=datetime.now(tz=UTC).isoformat().replace("+00:00", "Z"),
        total_return=simulation.stats.total_return,
        max_drawdown=simulation.stats.max_drawdown,
        sharpe=simulation.stats.sharpe,
        win_rate=simulation.stats.win_rate,
        candles=[_to_candle(item) for item in simulation.candles],
        trade_markers=[
            TradeMarker(
                id=trade.related_trade_id,
                timestamp=trade.timestamp,
                candle_timestamp=trade.candle_timestamp,
                action=trade.action,
                type=trade.action,
                side=trade.side,
                price=trade.price,
                qty=trade.qty,
                reason=trade.reason,
                related_trade_id=trade.related_trade_id,
                related_order_id=trade.related_order_id,
            )
            for trade in simulation.trades
        ],
        equity_curve=[EquityPoint(timestamp=item.timestamp, equity=item.equity) for item in simulation.equity_curve],
        chart_warnings=simulation.warnings,
    )


def _to_price_bar(candle: Candle) -> PriceBar:
    return PriceBar(
        timestamp=candle.timestamp,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
    )


def _to_candle(candle: PriceBar) -> Candle:
    return Candle(
        timestamp=candle.timestamp,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
    )


def _to_risk_envelope(controls: RiskControls) -> RiskEnvelope:
    return RiskEnvelope(
        max_open_positions=controls.max_open_positions,
        max_consecutive_loss=controls.max_consecutive_loss,
        max_symbol_exposure=controls.max_symbol_exposure,
        stop_loss_percent=controls.stop_loss_percent,
        max_trade_risk=controls.max_trade_risk,
        max_slippage_percent=controls.max_slippage_percent,
        max_spread_percent=controls.max_spread_percent,
        volatility_filter_percent=controls.volatility_filter_percent,
        max_position_notional=controls.max_position_notional,
        daily_loss_limit=controls.daily_loss_limit,
        max_leverage=controls.max_leverage,
        allowed_symbols=list(controls.allowed_symbols),
        trading_window_start=controls.trading_window_start,
        trading_window_end=controls.trading_window_end,
        kill_switch_enabled=controls.kill_switch_enabled,
        require_mark_price=controls.require_mark_price,
    )
