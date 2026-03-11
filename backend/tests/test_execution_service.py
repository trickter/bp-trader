from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.errors import ApplicationError
from app.application.services.live_execution_application_service import LiveExecutionApplicationService
from app.domain.shared.enums import PriceSource
from app.domain.strategy.entities import Strategy
from app.infrastructure.repositories.in_memory import InMemoryExecutionRuntimeRepository
from app.infrastructure.state import RuntimeState
from app.schema_read_models import Candle, Position, ProfileSummary
from app.schema_requests import ExecutionRuntimeCommand, LiveStrategyEnableRequest, RiskControls
from app.providers.base import AccountSnapshot, NormalizedList, NormalizedRecord


class MemoryState:
    pass


class StubExecutionGateway:
    async def submit_market_order(self, **kwargs):  # noqa: ANN003
        from app.schemas import ExecutionOrder

        now = "2026-03-10T00:00:00Z"
        return ExecutionOrder(
            id="ord_test",
            strategy_id="",
            strategy_name="",
            client_order_id=kwargs["client_order_id"],
            exchange_order_id="exch_test",
            symbol=kwargs["symbol"],
            side=kwargs["side"],
            action="market",
            status="submitted",
            quantity=kwargs["quantity"],
            price=0.0,
            reduce_only=kwargs["reduce_only"],
            submitted_at=now,
            updated_at=now,
        )


@pytest.fixture
def risk_controls() -> RiskControls:
    return RiskControls(
        max_open_positions=5,
        max_consecutive_loss=3,
        max_symbol_exposure=150.0,
        stop_loss_percent=10.0,
        max_trade_risk=10.0,
        max_slippage_percent=0.4,
        max_spread_percent=0.3,
        volatility_filter_percent=8.0,
        max_position_notional=300.0,
        daily_loss_limit=15.0,
        max_leverage=3.0,
        allowed_symbols=["BTC_USDC_PERP", "SOL_USDC_PERP"],
        trading_window_start="00:00",
        trading_window_end="23:59",
        kill_switch_enabled=False,
        require_mark_price=True,
        updated_at="2026-03-10T00:00:00Z",
    )


@pytest.fixture
def strategies() -> dict[str, Strategy]:
    strat_001 = Strategy.create(
            strategy_id="strat_001",
            name="Momentum Burst",
            kind="template",
            description="",
            market="BTC_USDC_PERP",
            account_id="acct_001",
            runtime="paper",
            status="healthy",
            price_source=PriceSource.LAST,
            parameters={
                "live_enabled": True,
                "execution_weight": 0.7,
                "poll_interval_seconds": 20,
                "fast_ema": 2,
                "slow_ema": 3,
                "template_preset_id": "ema_dual_trend",
                "timeframe": "15m",
            },
        )
    strat_001.last_backtest = "2026-03-10T00:00:00Z"
    strat_002 = Strategy.create(
            strategy_id="strat_002",
            name="Momentum Burst 2",
            kind="template",
            description="",
            market="SOL_USDC_PERP",
            account_id="acct_001",
            runtime="paper",
            status="healthy",
            price_source=PriceSource.LAST,
            parameters={"live_enabled": False, "execution_weight": 0.3, "poll_interval_seconds": 30, "fast_ema": 2, "slow_ema": 3, "template_preset_id": "ema_dual_trend", "timeframe": "15m"},
        )
    strat_002.last_backtest = "2026-03-10T00:00:00Z"
    strat_003 = Strategy.create(
            strategy_id="strat_003",
            name="Blocked",
            kind="template",
            description="",
            market="ETH_USDC_PERP",
            account_id="acct_001",
            runtime="paper",
            status="healthy",
            price_source=PriceSource.LAST,
            parameters={"live_enabled": False},
        )
    return {
        "strat_001": strat_001,
        "strat_002": strat_002,
        "strat_003": strat_003,
    }


def _build_service(
    strategies: dict[str, Strategy],
    risk_controls: RiskControls,
    *,
    positions: list[Position] | None = None,
) -> LiveExecutionApplicationService:
    strategy_repo = MagicMock()
    strategy_repo.list.side_effect = lambda: list(strategies.values())
    strategy_repo.get.side_effect = lambda strategy_id: strategies.get(strategy_id)
    strategy_repo.save.side_effect = lambda strategy: strategies.__setitem__(strategy.id, strategy) or strategy

    risk_repo = MagicMock()
    risk_repo.get.return_value = risk_controls

    operator_gateway = MagicMock()
    operator_gateway.fetch_profile_snapshot = AsyncMock(return_value=AccountSnapshot(
        summary=NormalizedRecord(
            data=ProfileSummary(
                total_equity=100.0,
                available_margin=100.0,
                unrealized_pnl=0.0,
                realized_pnl_24h=0.0,
                win_rate=50.0,
                risk_level="low",
                price_source=PriceSource.MARK,
                synced_at="2026-03-10T00:00:00Z",
            ),
            raw_payload={},
        ),
        assets=NormalizedList(items=[]),
        positions=NormalizedList(
            items=[
                NormalizedRecord(data=item, raw_payload={})
                for item in (positions or [])
            ]
        ),
    ))
    operator_gateway.fetch_klines = AsyncMock(return_value=NormalizedRecord(
        data=MagicMock(
            candles=[
                Candle(
                    timestamp=f"2026-03-10T{(index // 4):02d}:{(index % 4) * 15:02d}:00Z",
                    open=float(index + 1),
                    high=float(index + 2),
                    low=float(index + 1),
                    close=float(index + 2),
                    volume=10.0 + index,
                )
                for index in range(60)
            ]
        ),
        raw_payload={},
    ))

    runtime_repo = InMemoryExecutionRuntimeRepository(RuntimeState(MemoryState()))
    return LiveExecutionApplicationService(
        strategy_repository=strategy_repo,
        risk_controls_repository=risk_repo,
        operator_gateway=operator_gateway,
        execution_gateway=StubExecutionGateway(),
        runtime_repository=runtime_repo,
        settings_obj=MagicMock(backpack_mode="mock"),
    )


@pytest.mark.asyncio
async def test_enable_strategy_requires_whitelist(strategies, risk_controls) -> None:
    service = _build_service(strategies, risk_controls)

    with pytest.raises(ApplicationError, match="live trading"):
        service.enable_live_strategy("strat_003", LiveStrategyEnableRequest(confirmed=True))


@pytest.mark.asyncio
async def test_enable_and_disable_live_strategy(strategies, risk_controls) -> None:
    service = _build_service(strategies, risk_controls)

    enabled = service.enable_live_strategy("strat_001", LiveStrategyEnableRequest(confirmed=True))
    disabled = service.disable_live_strategy("strat_001")

    assert enabled.live_enabled is True
    assert disabled.live_enabled is False
    assert service.runtime_status().enabled_strategy_count == 0


@pytest.mark.asyncio
async def test_execution_cycle_submits_market_order(strategies, risk_controls, monkeypatch) -> None:
    service = _build_service(strategies, risk_controls)
    service.enable_live_strategy("strat_001", LiveStrategyEnableRequest(confirmed=True))

    async def fake_signal(*args, **kwargs):  # noqa: ANN002, ANN003
        return {"action": "open_long", "side": "Bid", "price": 4.0}

    monkeypatch.setattr(LiveExecutionApplicationService, "_generate_signal", fake_signal)

    await service.execute_cycle()

    orders = service.list_orders()
    assert len(orders) == 1
    assert orders[0].symbol == "BTC_USDC_PERP"
    assert orders[0].status == "submitted"


@pytest.mark.asyncio
async def test_runtime_limits_to_two_active_strategies(strategies, risk_controls) -> None:
    strategies["strat_002"] = strategies["strat_002"].update(
        name=strategies["strat_002"].name,
        kind=strategies["strat_002"].kind,
        description=strategies["strat_002"].description,
        market=strategies["strat_002"].market,
        account_id=strategies["strat_002"].account_id,
        runtime=strategies["strat_002"].runtime,
        status=strategies["strat_002"].status,
        price_source=strategies["strat_002"].price_source,
        parameters={**strategies["strat_002"].parameters, "live_enabled": True},
    )
    service = _build_service(strategies, risk_controls)
    service.enable_live_strategy("strat_001", LiveStrategyEnableRequest(confirmed=True))
    service.enable_live_strategy("strat_002", LiveStrategyEnableRequest(confirmed=True))

    runtime = service.runtime_status()
    assert runtime.enabled_strategy_count == 2
    assert runtime.max_concurrent_strategies == 2


@pytest.mark.asyncio
async def test_manual_flatten_submits_reduce_only_order(strategies, risk_controls) -> None:
    service = _build_service(
        strategies,
        risk_controls,
        positions=[
            Position(
                symbol="BTC_USDC_PERP",
                side="long",
                quantity=0.00426,
                entry_price=70330.8,
                mark_price=70437.4,
                liquidation_price=None,
                unrealized_pnl=0.0,
                margin_used=0.0,
                opened_at="2026-03-10T00:00:00Z",
                price_source=PriceSource.MARK,
            )
        ],
    )
    service.enable_live_strategy("strat_001", LiveStrategyEnableRequest(confirmed=True))

    result = await service.flatten_live_strategy(
        "strat_001",
        ExecutionRuntimeCommand(confirmed=True, reason="test flatten"),
    )

    orders = service.list_orders()
    assert result.last_signal == "manual_close"
    assert len(orders) == 1
    assert orders[0].reduce_only is True


@pytest.mark.asyncio
async def test_disable_and_flatten_marks_strategy_disabled(strategies, risk_controls) -> None:
    service = _build_service(
        strategies,
        risk_controls,
        positions=[
            Position(
                symbol="BTC_USDC_PERP",
                side="long",
                quantity=0.00426,
                entry_price=70330.8,
                mark_price=70437.4,
                liquidation_price=None,
                unrealized_pnl=0.0,
                margin_used=0.0,
                opened_at="2026-03-10T00:00:00Z",
                price_source=PriceSource.MARK,
            )
        ],
    )
    service.enable_live_strategy("strat_001", LiveStrategyEnableRequest(confirmed=True))

    result = await service.disable_and_flatten_live_strategy(
        "strat_001",
        ExecutionRuntimeCommand(confirmed=True, reason="test disable and flatten"),
    )

    assert result.live_enabled is False
    assert result.runtime_status == "disabled"
