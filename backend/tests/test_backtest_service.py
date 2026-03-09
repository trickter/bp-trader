"""Tests for backtest application service."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.application.services.backtest_application_service import BacktestApplicationService
from app.domain.shared.enums import PriceSource
from app.domain.strategy.entities import Strategy
from app.schemas import BacktestRequest, BacktestResult, RiskControls


# Test fixtures
@pytest.fixture
def mock_strategy_repository():
    """Create a mock strategy repository."""
    repo = MagicMock()
    strategy = Strategy(
        id="strat_001",
        name="Test Strategy",
        kind="template",
        market="BTC_USDC_PERP",
        runtime="python",
        status="active",
        price_source=PriceSource.MARK,
        description="Test strategy",
    )
    repo.get.return_value = strategy
    return repo


@pytest.fixture
def mock_backtest_repository():
    """Create a mock backtest repository."""
    repo = MagicMock()
    result = MagicMock(spec=BacktestResult)
    result.id = "test-backtest-id"
    repo.get.return_value = result
    repo.save_result.return_value = result
    return repo


@pytest.fixture
def mock_risk_controls_repository():
    """Create a mock risk controls repository."""
    repo = MagicMock()
    repo.get.return_value = RiskControls(
        max_open_positions=5,
        max_consecutive_loss=3,
        max_symbol_exposure=0.1,
        stop_loss_percent=5.0,
        max_trade_risk=0.02,
        max_slippage_percent=0.5,
        max_spread_percent=0.1,
        volatility_filter_percent=10.0,
        max_position_notional=10000.0,
        daily_loss_limit=1000.0,
        max_leverage=10.0,
        allowed_symbols=["BTC_USDC_PERP"],
        trading_window_start="00:00",
        trading_window_end="23:59",
        kill_switch_enabled=False,
        require_mark_price=True,
        updated_at="2024-01-15T10:30:00Z",
    )
    return repo


@pytest.fixture
def mock_operator_gateway():
    """Create a mock operator gateway."""
    from app.providers.base import NormalizedRecord
    from app.schemas import KlineResponse, Candle

    gateway = MagicMock()
    kline_response = KlineResponse(
        symbol="BTC_USDC_PERP",
        interval="1h",
        start_time=1704067200,
        end_time=1704153600,
        price_source=PriceSource.MARK,
        candles=[
            Candle(timestamp=1704067200, open=42000.0, high=42500.0, low=41800.0, close=42300.0, volume=1000.0),
            Candle(timestamp=1704070800, open=42300.0, high=42800.0, low=42100.0, close=42600.0, volume=1200.0),
        ],
    )
    gateway.fetch_klines = AsyncMock(return_value=NormalizedRecord(data=kline_response, raw_payload={}))
    gateway.fetch_exchange_accounts = AsyncMock(return_value=MagicMock(items=[]))
    return gateway


@pytest.fixture
def mock_acceptance_factory():
    """Create a mock acceptance factory."""
    factory = MagicMock()
    from app.schemas import BacktestRunAccepted
    factory.build.return_value = BacktestRunAccepted(
        id="test-acceptance-id",
        strategy_id="strat_001",
        strategy_kind="template",
        status="completed",
        created_at="2024-01-15T10:30:00Z",
        result_path="/api/backtests/test-acceptance-id",
    )
    return factory


@pytest.fixture
def backtest_service(
    mock_strategy_repository,
    mock_backtest_repository,
    mock_risk_controls_repository,
    mock_operator_gateway,
    mock_acceptance_factory,
):
    """Create backtest application service with mocks."""
    return BacktestApplicationService(
        strategy_repository=mock_strategy_repository,
        backtest_repository=mock_backtest_repository,
        risk_controls_repository=mock_risk_controls_repository,
        operator_gateway=mock_operator_gateway,
        acceptance_factory=mock_acceptance_factory,
        exchange_id="backpack",
        market_type="perp",
        demo_mode=True,
    )


class TestBacktestApplicationService:
    """Tests for BacktestApplicationService."""

    @pytest.mark.asyncio
    async def test_create_run(self, backtest_service) -> None:
        """Test creating a backtest run."""
        request = BacktestRequest(
            symbol="BTC_USDC_PERP",
            interval="1h",
            start_time=1704067200,
            end_time=1704153600,
            price_source=PriceSource.MARK,
            fee_bps=2,
            slippage_bps=4,
        )

        result = await backtest_service.create_run(
            strategy_id="strat_001",
            strategy_kind="template",
            request=request,
        )

        assert result.strategy_id == "strat_001"
        assert result.strategy_kind == "template"
        assert result.status == "completed"

    def test_get_existing_run(self, backtest_service) -> None:
        """Test getting an existing backtest run."""
        result = backtest_service.get_run("test-backtest-id")

        assert result.id == "test-backtest-id"

    def test_get_nonexistent_run_raises(self, backtest_service) -> None:
        """Test that getting a non-existent run raises NotFoundError."""
        from app.domain.shared.errors import NotFoundError

        backtest_service._backtest_repository.get.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            backtest_service.get_run("nonexistent")

        assert exc_info.value.code == "backtest_not_found"

    @pytest.mark.asyncio
    async def test_create_run_with_nonexistent_strategy(self, backtest_service) -> None:
        """Test that creating a run with non-existent strategy raises NotFoundError."""
        from app.domain.shared.errors import NotFoundError

        backtest_service._strategy_repository.get.return_value = None

        request = BacktestRequest(
            symbol="BTC_USDC_PERP",
            interval="1h",
            start_time=1704067200,
            end_time=1704153600,
            price_source=PriceSource.MARK,
            fee_bps=2,
            slippage_bps=4,
        )

        with pytest.raises(NotFoundError) as exc_info:
            await backtest_service.create_run(
                strategy_id="nonexistent",
                strategy_kind="template",
                request=request,
            )

        assert exc_info.value.code == "strategy_not_found"


class TestBacktestRequestSchema:
    """Tests for BacktestRequest schema validation."""

    def test_valid_backtest_request(self) -> None:
        """Test creating a valid BacktestRequest."""
        request = BacktestRequest(
            symbol="BTC_USDC_PERP",
            interval="1h",
            start_time=1704067200,
            end_time=1704153600,
            price_source=PriceSource.MARK,
            fee_bps=2,
            slippage_bps=4,
        )

        assert request.symbol == "BTC_USDC_PERP"
        assert request.interval == "1h"
        assert request.price_source == PriceSource.MARK

    def test_backtest_request_defaults(self) -> None:
        """Test BacktestRequest default values."""
        request = BacktestRequest(
            symbol="BTC_USDC_PERP",
            interval="1h",
            start_time=1704067200,
            end_time=1704153600,
            price_source=PriceSource.MARK,
            fee_bps=0,
            slippage_bps=0,
        )

        assert request.fee_bps == 0
        assert request.slippage_bps == 0
