"""Tests for application services - Business logic layer."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.application.services.operator_query_service import OperatorQueryService
from app.application.ports.repositories import QuantOperatorGateway, RiskControlsRepository
from app.providers.base import NormalizedList
from app.schema_requests import RiskControls
from app.schemas import AgentCapability


# Test fixtures
@pytest.fixture
def mock_gateway():
    """Create a mock operator gateway."""
    gateway = MagicMock(spec=QuantOperatorGateway)
    gateway.market_symbols = MagicMock(return_value=["BTC_USDC_PERP", "SOL_USDC_PERP"])
    return gateway


@pytest.fixture
def mock_risk_controls_repo():
    """Create a mock risk controls repository."""
    repo = MagicMock(spec=RiskControlsRepository)
    risk_controls = RiskControls(
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
    repo.get.return_value = risk_controls
    return repo


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = MagicMock()
    settings.backpack_mode = "mock"
    settings.backpack_default_symbol = "BTC_USDC_PERP"
    return settings


@pytest.fixture
def operator_service(mock_gateway, mock_risk_controls_repo, mock_settings):
    """Create operator query service with mocks."""
    return OperatorQueryService(
        gateway=mock_gateway,
        risk_controls_repository=mock_risk_controls_repo,
        settings_obj=mock_settings,
        default_symbol="BTC_USDC_PERP",
    )


class TestOperatorQueryService:
    """Tests for OperatorQueryService."""

    def test_market_symbols(self, operator_service) -> None:
        """Test market symbols retrieval."""
        result = operator_service.market_symbols()

        assert "BTC_USDC_PERP" in result
        assert "SOL_USDC_PERP" in result

    def test_risk_controls(self, operator_service) -> None:
        """Test risk controls retrieval."""
        result = operator_service.risk_controls()

        assert result["maxOpenPositions"] == 5
        assert result["maxConsecutiveLoss"] == 3

    def test_capabilities(self, operator_service) -> None:
        """Test capabilities listing."""
        result = OperatorQueryService.capabilities()

        assert len(result) > 0
        assert any(cap.id == "profile.summary.read" for cap in result)
        assert any(cap.id == "strategies.read" for cap in result)


class TestCapabilities:
    """Tests for capability definitions."""

    def test_all_capabilities_have_required_fields(self) -> None:
        """Test that all capabilities have required fields."""
        capabilities = OperatorQueryService.capabilities()

        for cap in capabilities:
            assert hasattr(cap, "id")
            assert hasattr(cap, "label")
            assert hasattr(cap, "description")
            assert hasattr(cap, "route")

    def test_capabilities_are_valid_agent_capability_type(self) -> None:
        """Test that capabilities are valid AgentCapability objects."""
        capabilities = OperatorQueryService.capabilities()

        for cap in capabilities:
            assert isinstance(cap, AgentCapability)
