"""Tests for providers module - Exchange adapters."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.providers.base import (
    AccountSnapshot,
    NormalizedList,
    NormalizedRecord,
    ProviderError,
)
from app.providers import BackpackProvider
from app.schema_read_models import (
    ProfileSummary,
    AssetBalance,
    Position,
)
from app.domain.shared.enums import PriceSource


# Sample test data
SAMPLE_PROFILE_SUMMARY = ProfileSummary(
    id="test-account",
    account_id="test-account",
    equity=10000.0,
    available_margin=8000.0,
    realized_pnl_24h=150.0,
    unrealized_pnl=50.0,
    total_pnl=200.0,
    win_rate=0.65,
    updated_at="2024-01-15T10:30:00Z",
)

SAMPLE_ASSETS = [
    AssetBalance(
        asset="USDC",
        available=5000.0,
        locked=100.0,
        usd_value=5100.0,
    ),
    AssetBalance(
        asset="SOL",
        available=10.0,
        locked=2.0,
        usd_value=4900.0,
    ),
]

SAMPLE_POSITIONS = [
    Position(
        symbol="SOL-PERP",
        side="long",
        quantity=10.0,
        entry_price=490.0,
        mark_price=495.0,
        unrealized_pnl=50.0,
        margin_used=1000.0,
        opened_at="2024-01-10T08:00:00Z",
    ),
]


class TestNormalizedRecord:
    """Tests for NormalizedRecord dataclass."""

    def test_normalized_record_creation(self) -> None:
        """Test NormalizedRecord can be created with data."""
        record = NormalizedRecord(
            data=SAMPLE_PROFILE_SUMMARY,
            raw_payload={"id": "test", "equity": 10000.0},
        )
        assert record.data == SAMPLE_PROFILE_SUMMARY
        assert record.raw_payload["equity"] == 10000.0

    def test_normalized_record_with_warnings(self) -> None:
        """Test NormalizedRecord can include warnings."""
        record = NormalizedRecord(
            data=SAMPLE_PROFILE_SUMMARY,
            raw_payload={},
            warnings=["Warning 1"],
        )
        assert len(record.warnings) == 1
        assert "Warning 1" in record.warnings


class TestNormalizedList:
    """Tests for NormalizedList dataclass."""

    def test_normalized_list_creation(self) -> None:
        """Test NormalizedList can be created with items."""
        records = [
            NormalizedRecord(data=asset, raw_payload=asset.model_dump())
            for asset in SAMPLE_ASSETS
        ]
        normalized_list = NormalizedList(items=records)
        assert len(normalized_list.items) == 2

    def test_normalized_list_with_warnings(self) -> None:
        """Test NormalizedList can include warnings."""
        records = [
            NormalizedRecord(data=asset, raw_payload=asset.model_dump())
            for asset in SAMPLE_ASSETS
        ]
        normalized_list = NormalizedList(items=records, warnings=["Data warning"])
        assert len(normalized_list.warnings) == 1


class TestAccountSnapshot:
    """Tests for AccountSnapshot dataclass."""

    def test_account_snapshot_creation(self) -> None:
        """Test AccountSnapshot can be created with all fields."""
        summary_record = NormalizedRecord(
            data=SAMPLE_PROFILE_SUMMARY,
            raw_payload=SAMPLE_PROFILE_SUMMARY.model_dump(),
        )
        asset_records = [
            NormalizedRecord(data=asset, raw_payload=asset.model_dump())
            for asset in SAMPLE_ASSETS
        ]
        position_records = [
            NormalizedRecord(data=pos, raw_payload=pos.model_dump())
            for pos in SAMPLE_POSITIONS
        ]

        snapshot = AccountSnapshot(
            summary=summary_record,
            assets=NormalizedList(items=asset_records),
            positions=NormalizedList(items=position_records),
        )

        assert snapshot.summary.data == SAMPLE_PROFILE_SUMMARY
        assert len(snapshot.assets.items) == 2
        assert len(snapshot.positions.items) == 1


class TestProviderError:
    """Tests for ProviderError."""

    def test_provider_error_creation(self) -> None:
        """Test ProviderError can be raised."""
        with pytest.raises(ProviderError) as exc_info:
            raise ProviderError("Test error")

        assert str(exc_info.value) == "Test error"
