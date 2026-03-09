"""Tests for strategy application service."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.application.services.strategy_application_service import StrategyApplicationService
from app.domain.shared.errors import NotFoundError
from app.domain.shared.enums import PriceSource
from app.domain.strategy.entities import Strategy
from app.schemas import StrategyUpsertRequest


# Test fixtures
@pytest.fixture
def mock_repository():
    """Create a mock strategy repository."""
    repo = MagicMock()

    # Pre-populate with test strategies
    strategies = [
        Strategy(
            id="strat_001",
            name="Test Strategy 1",
            kind="template",
            market="BTC_USDC_PERP",
            runtime="python",
            status="active",
            price_source=PriceSource.MARK,
            description="Test strategy 1",
            last_backtest="2024-01-15",
            sharpe=1.5,
        ),
        Strategy(
            id="strat_002",
            name="Test Strategy 2",
            kind="script",
            market="SOL_USDC_PERP",
            runtime="javascript",
            status="paused",
            price_source=PriceSource.LAST,
            description="Test strategy 2",
        ),
    ]

    def list_strategies():
        return strategies

    def get_strategy(strategy_id):
        for s in strategies:
            if s.id == strategy_id:
                return s
        return None

    def save_strategy(strategy):
        # Update or add
        for i, s in enumerate(strategies):
            if s.id == strategy.id:
                strategies[i] = strategy
                return strategy
        strategies.append(strategy)
        return strategy

    repo.list = list_strategies
    repo.get = get_strategy
    repo.save = save_strategy

    return repo


@pytest.fixture
def strategy_service(mock_repository):
    """Create strategy application service with mock repository."""
    return StrategyApplicationService(strategy_repository=mock_repository)


class TestStrategyApplicationService:
    """Tests for StrategyApplicationService."""

    def test_list_strategies(self, strategy_service) -> None:
        """Test listing all strategies."""
        result = strategy_service.list_strategies()

        assert len(result) == 2
        assert result[0].id == "strat_001"
        assert result[1].id == "strat_002"

    def test_get_existing_strategy(self, strategy_service) -> None:
        """Test getting an existing strategy."""
        result = strategy_service.get_strategy("strat_001")

        assert result.id == "strat_001"
        assert result.name == "Test Strategy 1"

    def test_get_nonexistent_strategy_raises(self, strategy_service) -> None:
        """Test that getting a non-existent strategy raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            strategy_service.get_strategy("nonexistent")

        assert exc_info.value.code == "strategy_not_found"

    def test_create_strategy(self, strategy_service) -> None:
        """Test creating a new strategy."""
        payload = StrategyUpsertRequest(
            name="New Strategy",
            kind="template",
            description="A new test strategy",
            market="ETH_USDC_PERP",
            runtime="python",
            status="active",
            price_source=PriceSource.MARK,
        )

        result = strategy_service.create_strategy(payload)

        assert result.name == "New Strategy"
        assert result.kind == "template"
        assert result.market == "ETH_USDC_PERP"
        assert result.id.startswith("strat_")

    def test_update_strategy(self, strategy_service) -> None:
        """Test updating an existing strategy."""
        payload = StrategyUpsertRequest(
            name="Updated Strategy",
            kind="template",
            description="Updated description",
            market="BTC_USDC_PERP",
            runtime="python",
            status="paused",
            price_source=PriceSource.LAST,
        )

        result = strategy_service.update_strategy("strat_001", payload)

        assert result.name == "Updated Strategy"
        assert result.status == "paused"
        assert result.id == "strat_001"

    def test_update_nonexistent_strategy_raises(self, strategy_service) -> None:
        """Test that updating a non-existent strategy raises NotFoundError."""
        payload = StrategyUpsertRequest(
            name="Test",
            kind="template",
            description="",
            market="BTC_USDC_PERP",
            runtime="python",
            status="active",
            price_source=PriceSource.MARK,
        )

        with pytest.raises(NotFoundError) as exc_info:
            strategy_service.update_strategy("nonexistent", payload)

        assert exc_info.value.code == "strategy_not_found"

    def test_ensure_exists_returns_strategy(self, strategy_service) -> None:
        """Test that ensure_exists returns a strategy if it exists."""
        result = strategy_service.ensure_exists("strat_001")

        assert result.id == "strat_001"

    def test_ensure_exists_raises_for_missing(self, strategy_service) -> None:
        """Test that ensure_exists raises if strategy doesn't exist."""
        with pytest.raises(NotFoundError):
            strategy_service.ensure_exists("nonexistent")


class TestStrategyEntity:
    """Tests for Strategy entity."""

    def test_create_strategy(self) -> None:
        """Test creating a Strategy entity."""
        strategy = Strategy.create(
            strategy_id="test_id",
            name="Test",
            kind="template",
            description="Test description",
            market="BTC_USDC_PERP",
            account_id="acc_001",
            runtime="python",
            status="active",
            price_source=PriceSource.MARK,
            parameters={"param1": "value1"},
        )

        assert strategy.id == "test_id"
        assert strategy.name == "Test"
        assert strategy.parameters["param1"] == "value1"

    def test_update_strategy(self) -> None:
        """Test updating a Strategy entity."""
        strategy = Strategy.create(
            strategy_id="test_id",
            name="Original",
            kind="template",
            description="Original",
            market="BTC_USDC_PERP",
            account_id="",
            runtime="python",
            status="active",
            price_source=PriceSource.MARK,
            parameters={},
        )

        updated = strategy.update(
            name="Updated",
            kind="script",
            description="Updated",
            market="SOL_USDC_PERP",
            account_id="acc_002",
            runtime="javascript",
            status="paused",
            price_source=PriceSource.LAST,
            parameters={"new_param": 123},
        )

        assert updated.id == "test_id"  # ID preserved
        assert updated.name == "Updated"
        assert updated.last_backtest == ""  # Preserved from original


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_not_found_error_properties(self) -> None:
        """Test NotFoundError has correct properties."""
        error = NotFoundError(code="test_code", message="Test message")

        assert error.code == "test_code"
        assert error.message == "Test message"
        assert str(error) == "Test message"
