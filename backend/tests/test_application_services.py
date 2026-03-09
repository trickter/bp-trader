"""Tests for application services - Business logic layer."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.application.services.operator_query_service import OperatorQueryService
from app.application.ports.repositories import QuantOperatorGateway, RiskControlsRepository
from app.providers.base import AccountSnapshot, NormalizedList, NormalizedRecord
from app.schema_read_models import (
    ProfileSummary,
    AssetBalance,
    Position,
    RiskControls,
)
from app.domain.shared.enums import PriceSource
from app.schemas import AgentCapability


# Test fixtures
@pytest.fixture
def mock_gateway():
    """Create a mock operator gateway."""
    gateway = MagicMock(spec=QuantOperatorGateway)

    # Mock profile snapshot
    summary = ProfileSummary(
        id="test",
        account_id="test",
        equity=10000.0,
        available_margin=8000.0,
        realized_pnl_24h=150.0,
        unrealized_pnl=50.0,
        total_pnl=200.0,
        win_rate=0.65,
        updated_at="2024-01-15T10:30:00Z",
    )
    snapshot = AccountSnapshot(
        summary=NormalizedRecord(data=summary, raw_payload={}),
        assets=NormalizedList(items=[
            NormalizedRecord(data=AssetBalance(asset="USDC", available=5000.0, locked=100.0, usd_value=5100.0), raw_payload={}),
        ]),
        positions=NormalizedList(items=[
            NormalizedRecord(data=Position(symbol="SOL-PERP", side="long", quantity=10.0, entry_price=490.0, mark_price=495.0, unrealized_pnl=50.0, margin_used=1000.0, opened_at="2024-01-10T08:00:00Z"), raw_payload={}),
        ]),
    )
    gateway.fetch_profile_snapshot = AsyncMock(return_value=snapshot)
    gateway.fetch_account_events = AsyncMock(return_value=NormalizedList(items=[]))
    gateway.fetch_market_pulse = AsyncMock(return_value=NormalizedList(items=[]))
    gateway.fetch_exchange_accounts = AsyncMock(return_value=NormalizedList(items=[]))
    gateway.fetch_klines = AsyncMock(return_value=MagicMock(data=MagicMock()))
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
        allowed_symbols=["BTC_USDC_PERP", "SOL_USDC_PERP"],
        trading_window_start="00:00",
        trading_window_end="23:59",
        kill_switch_enabled=False,
        require_mark_price=True,
        updated_at="2024-01-15T10:30:00Z",
    )
    repo.get.return_value = risk_controls
    repo.save.return_value = risk_controls
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

    @pytest.mark.asyncio
    async def test_profile_summary(self, operator_service) -> None:
        """Test profile summary retrieval."""
        result = await operator_service.profile_summary()

        assert result["equity"] == 10000.0
        assert result["availableMargin"] == 8000.0
        assert result["realizedPnl24h"] == 150.0

    @pytest.mark.asyncio
    async def test_profile_assets(self, operator_service) -> None:
        """Test profile assets retrieval."""
        result = await operator_service.profile_assets()

        assert len(result) == 1
        assert result[0]["asset"] == "USDC"

    @pytest.mark.asyncio
    async def test_profile_positions(self, operator_service) -> None:
        """Test profile positions retrieval."""
        result = await operator_service.profile_positions()

        assert len(result) == 1
        assert result[0]["symbol"] == "SOL-PERP"

    @pytest.mark.asyncio
    async def test_profile_account_events(self, operator_service) -> None:
        """Test account events retrieval."""
        result = await operator_service.profile_account_events()

        assert isinstance(result, list)

    def test_market_symbols(self, operator_service) -> None:
        """Test market symbols retrieval."""
        result = operator_service.market_symbols()

        assert "BTC_USDC_PERP" in result
        assert "SOL_USDC_PERP" in result

    @pytest.mark.asyncio
    async def test_exchange_accounts(self, operator_service) -> None:
        """Test exchange accounts retrieval."""
        result = await operator_service.exchange_accounts()

        assert isinstance(result, list)

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

    @pytest.mark.asyncio
    async def test_agent_context(self, operator_service) -> None:
        """Test agent context generation."""
        result = await operator_service.agent_context()

        assert result["accountMode"] == "mock"
        assert "profile.summary.read" in result["availableCapabilities"]
        assert result["resources"]["profileSummary"] == "/api/profile/summary"


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
