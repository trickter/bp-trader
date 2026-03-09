"""Tests for backtest application service."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.schemas import BacktestRequest, RiskControls


class TestBacktestRequestSchema:
    """Tests for BacktestRequest schema validation."""

    def test_valid_backtest_request(self) -> None:
        """Test creating a valid BacktestRequest."""
        from app.domain.shared.enums import PriceSource

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
        from app.domain.shared.enums import PriceSource

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
