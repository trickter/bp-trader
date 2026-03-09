from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from ...domain.backtest.entities import BacktestSpec, PriceBar, RiskEnvelope, StrategySnapshot
from ...domain.backtest.service import simulate_backtest
from ...domain.shared.errors import NotFoundError
from ...schemas import BacktestRequest, BacktestResult, BacktestRunAccepted, Candle, EquityPoint, RiskControls, StrategySummary, TradeMarker
from ..ports.repositories import BacktestAcceptanceFactory, BacktestRunRepository, QuantOperatorGateway, RiskControlsRepository, StrategyRepository


@dataclass(slots=True)
class BacktestApplicationService:
    strategy_repository: StrategyRepository
    backtest_repository: BacktestRunRepository
    risk_controls_repository: RiskControlsRepository
    operator_gateway: QuantOperatorGateway
    acceptance_factory: BacktestAcceptanceFactory
    exchange_id: str
    market_type: str
    demo_mode: bool

    async def create_run(
        self,
        *,
        strategy_id: str,
        strategy_kind: str,
        request: BacktestRequest,
    ) -> BacktestRunAccepted:
        strategy = self._require_strategy(strategy_id)
        created_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
        backtest_id = f"{strategy_kind}-{strategy_id}-{uuid4().hex[:8]}"
        result = await self._build_result(
            backtest_id=backtest_id,
            strategy=self._to_summary(strategy),
            request=request,
            created_at=created_at,
        )
        self.backtest_repository.save_result(result)
        return self.acceptance_factory.build(
            backtest_id=backtest_id,
            strategy_id=strategy_id,
            strategy_kind=strategy_kind,
            created_at=created_at,
            demo_mode=self.demo_mode,
        )

    def get_run(self, backtest_id: str) -> BacktestResult:
        result = self.backtest_repository.get(backtest_id)
        if result is None:
            raise NotFoundError(code="backtest_not_found", message="Backtest run does not exist.")
        return result

    async def _build_result(
        self,
        *,
        backtest_id: str,
        strategy: StrategySummary,
        request: BacktestRequest,
        created_at: str,
    ) -> BacktestResult:
        kline_payload = await self.operator_gateway.fetch_klines(
            symbol=request.symbol,
            interval=request.interval,
            start_time=request.start_time,
            end_time=request.end_time,
            price_source=request.price_source,
        )
        risk_controls = self.risk_controls_repository.get()
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
            candles=[_to_price_bar(item) for item in kline_payload.data.candles],
        )
        completed_at = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
        return BacktestResult(
            id=backtest_id,
            strategy_id=strategy.id,
            strategy_kind=strategy.kind,
            strategy_name=strategy.name,
            exchange_id=self.exchange_id,
            market_type=self.market_type,
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
            completed_at=completed_at,
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

    def _require_strategy(self, strategy_id: str):
        strategy = self.strategy_repository.get(strategy_id)
        if strategy is None:
            raise NotFoundError(code="strategy_not_found", message="Strategy does not exist.")
        return strategy

    @staticmethod
    def _to_summary(strategy) -> StrategySummary:
        return StrategySummary(
            id=strategy.id,
            name=strategy.name,
            kind=strategy.kind,
            description=strategy.description,
            market=strategy.market,
            account_id=strategy.account_id,
            runtime=strategy.runtime,
            status=strategy.status,
            last_backtest=strategy.last_backtest,
            sharpe=strategy.sharpe,
            price_source=strategy.price_source,
            parameters=strategy.parameters,
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
