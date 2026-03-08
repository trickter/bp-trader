"""Tests for Backpack data normalization."""
from __future__ import annotations

import pytest
from datetime import datetime

from app.providers.backpack import (
    BackpackProvider,
    _unwrap_object,
    _unwrap_list,
    _pick,
    _floatify,
    _stringify,
    _normalize_symbol,
    _infer_side,
    _coerce_timestamp,
    _map_event_type,
)
from app.schemas import EventType, EventOrigin, PriceSource


# Import test fixtures
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from conftest import (
    SAMPLE_ACCOUNT_RESPONSE,
    SAMPLE_CAPITAL_RESPONSE,
    SAMPLE_COLLATERAL_RESPONSE,
    SAMPLE_POSITIONS_RESPONSE,
    SAMPLE_FILLS_RESPONSE,
    SAMPLE_FUNDING_RESPONSE,
    SAMPLE_MARKET_RESPONSE,
)


class TestUnwrapObject:
    """Tests for _unwrap_object helper."""

    def test_returns_direct_mapping(self):
        """Test returns direct mapping."""
        result = _unwrap_object({"key": "value"})
        assert result == {"key": "value"}

    def test_unwraps_data_key(self):
        """Test unwraps 'data' key."""
        result = _unwrap_object({"data": {"key": "value"}})
        assert result == {"key": "value"}

    def test_unwraps_result_key(self):
        """Test unwraps 'result' key."""
        result = _unwrap_object({"result": {"key": "value"}})
        assert result == {"key": "value"}

    def test_returns_empty_for_invalid(self):
        """Test returns empty dict for invalid input."""
        assert _unwrap_object(None) == {}
        assert _unwrap_object("string") == {}
        assert _unwrap_object([1, 2, 3]) == {}


class TestUnwrapList:
    """Tests for _unwrap_list helper."""

    def test_returns_direct_list(self):
        """Test returns direct list."""
        result = _unwrap_list([{"a": 1}, {"b": 2}])
        assert len(result) == 2

    def test_unwraps_items_key(self):
        """Test unwraps 'items' key."""
        result = _unwrap_list({"items": [{"a": 1}]})
        assert result == [{"a": 1}]

    def test_filters_non_dict_items(self):
        """Test filters out non-dict items."""
        result = _unwrap_list([{"a": 1}, "string", 123, None])
        assert len(result) == 1


class TestPick:
    """Tests for _pick helper."""

    def test_finds_first_matching_key(self):
        """Test finds first matching key."""
        payload = {"a": 1, "b": 2, "c": 3}
        result = _pick(payload, "b", "a", "c")
        assert result == 2

    def test_returns_none_if_no_match(self):
        """Test returns None if no key matches."""
        payload = {"a": 1}
        result = _pick(payload, "x", "y", "z")
        assert result is None

    def test_ignores_none_values(self):
        """Test ignores keys with None values."""
        payload = {"a": None, "b": 2}
        result = _pick(payload, "a", "b")
        assert result == 2


class TestFloatify:
    """Tests for _floatify helper."""

    def test_converts_int(self):
        """Test converts int to float."""
        assert _floatify(123) == 123.0

    def test_converts_string_number(self):
        """Test converts string number."""
        assert _floatify("123.45") == 123.45

    def test_handles_none(self):
        """Test handles None."""
        assert _floatify(None) == 0.0

    def test_handles_empty_string(self):
        """Test handles empty string."""
        assert _floatify("") == 0.0

    def test_handles_bool(self):
        """Test converts bool to float."""
        assert _floatify(True) == 1.0
        assert _floatify(False) == 0.0


class TestStringify:
    """Tests for _stringify helper."""

    def test_converts_string(self):
        """Test returns string as-is."""
        assert _stringify("hello") == "hello"

    def test_handles_none(self):
        """Test returns fallback for None."""
        assert _stringify(None, fallback="default") == "default"

    def test_handles_empty_string(self):
        """Test returns fallback for empty string."""
        assert _stringify("  ", fallback="default") == "default"


class TestNormalizeSymbol:
    """Tests for symbol normalization."""

    def test_picks_symbol_key(self):
        """Test picks 'symbol' key."""
        payload = {"symbol": "SOL-PERP"}
        assert _normalize_symbol(payload) == "SOL-PERP"

    def test_picks_market_key(self):
        """Test picks 'market' key."""
        payload = {"market": "BTC-PERP"}
        assert _normalize_symbol(payload) == "BTC-PERP"

    def test_returns_unknown_for_missing(self):
        """Test returns UNKNOWN for missing symbol."""
        assert _normalize_symbol({}) == "UNKNOWN"


class TestInferSide:
    """Tests for side inference."""

    def test_picks_explicit_side(self):
        """Test picks explicit 'long' side."""
        payload = {"side": "long", "quantity": 10.0}
        assert _infer_side(payload, 10.0) == "long"

    def test_infers_from_positive_quantity(self):
        """Test infers long from positive quantity."""
        payload = {"quantity": 10.0}
        assert _infer_side(payload, 10.0) == "long"

    def test_infers_from_negative_quantity(self):
        """Test infers short from negative quantity."""
        payload = {"quantity": -10.0}
        assert _infer_side(payload, 10.0) == "short"


class TestCoerceTimestamp:
    """Tests for timestamp coercion."""

    def test_handles_iso_string(self):
        """Test handles ISO string."""
        result = _coerce_timestamp("2024-01-15T10:30:00Z")
        assert result is not None
        assert "2024-01-15" in result

    def test_handles_milliseconds(self):
        """Test handles milliseconds timestamp."""
        result = _coerce_timestamp(1705312800000)
        assert result is not None
        assert "2024-01-15" in result

    def test_handles_none(self):
        """Test returns None for None."""
        assert _coerce_timestamp(None) is None

    def test_handles_empty_string(self):
        """Test returns None for empty string."""
        assert _coerce_timestamp("") is None


class TestMapEventType:
    """Tests for event type mapping."""

    def test_maps_liquidation(self):
        """Test maps liquidation events."""
        assert _map_event_type("liquidation") == EventType.LIQUIDATION
        assert _map_event_type("LIQUIDATION") == EventType.LIQUIDATION

    def test_maps_adl(self):
        """Test maps ADL events."""
        assert _map_event_type("adl") == EventType.ADL

    def test_maps_funding(self):
        """Test maps funding events."""
        assert _map_event_type("funding") == EventType.FUNDING_SETTLEMENT

    def test_maps_fee(self):
        """Test maps fee events."""
        assert _map_event_type("fee") == EventType.FEE_CHARGE

    def test_maps_default_to_trade(self):
        """Test default to trade fill."""
        assert _map_event_type("trade") == EventType.TRADE_FILL
        assert _map_event_type("unknown") == EventType.TRADE_FILL


class TestPositionNormalization:
    """Tests for position normalization (the core business logic)."""

    def test_normalize_position_with_all_fields(self):
        """Test normalizing a position with all common field variants."""
        from app.providers.backpack import BackpackProvider

        # Test various field name variants
        test_cases = [
            # (payload, expected_symbol)
            ({"symbol": "SOL-PERP", "quantity": 10.0, "entryPrice": 500.0, "markPrice": 510.0}, "SOL-PERP"),
            ({"market": "BTC-PERP", "qty": 5.0, "avgEntryPrice": 40000.0, "mark_price": 41000.0}, "BTC-PERP"),
            ({"product": "ETH-PERP", "position_size": 20.0, "average_entry_price": 2000.0, "mark": 2100.0}, "ETH-PERP"),
        ]

        provider = BackpackProvider.__new__(BackpackProvider)

        for payload, expected_symbol in test_cases:
            payload.update({
                "unrealizedPnl": 100.0,
                "marginUsed": 1000.0,
                "side": "long",
                "openedAt": "2024-01-15T10:30:00Z",
            })
            positions = provider._normalize_positions([payload], PriceSource.MARK)
            assert len(positions.items) == 1
            assert positions.items[0].data.symbol == expected_symbol

    def test_position_side_inference(self):
        """Test position side is correctly inferred."""
        from app.providers.backpack import BackpackProvider

        provider = BackpackProvider.__new__(BackpackProvider)

        # Long case: positive quantity with no side
        payload = {
            "symbol": "SOL-PERP",
            "quantity": 10.0,
            "netQuantity": 10.0,
            "entryPrice": 500.0,
            "markPrice": 510.0,
            "unrealizedPnl": 100.0,
            "marginUsed": 1000.0,
        }
        positions = provider._normalize_positions([payload], PriceSource.MARK)
        assert positions.items[0].data.side == "long"

        # Short case: negative netQuantity
        payload["netQuantity"] = -10.0
        positions = provider._normalize_positions([payload], PriceSource.MARK)
        assert positions.items[0].data.side == "short"


class TestAssetNormalization:
    """Tests for asset/balance normalization."""

    def test_assets_combined_from_capital_and_collateral(self):
        """Test assets are combined from both capital and collateral responses."""
        from app.providers.backpack import BackpackProvider

        provider = BackpackProvider.__new__(BackpackProvider)

        assets = provider._normalize_assets(
            capital_rows=SAMPLE_CAPITAL_RESPONSE,
            collateral_rows=SAMPLE_COLLATERAL_RESPONSE,
            price_source=PriceSource.MARK,
        )

        # Should have 2 assets
        assert len(assets.items) == 2

        # Check USDC asset has combined values
        usdc = next(item for item in assets.items if item.data.asset == "USDC")
        assert usdc.data.available == 5000.0
        assert usdc.data.locked == 100.0
        assert usdc.data.collateral_value == 5100.0

    def test_portfolio_weights_sum_to_100(self):
        """Test portfolio weights sum to 100%."""
        from app.providers.backpack import BackpackProvider

        provider = BackpackProvider.__new__(BackpackProvider)

        assets = provider._normalize_assets(
            capital_rows=SAMPLE_CAPITAL_RESPONSE,
            collateral_rows=SAMPLE_COLLATERAL_RESPONSE,
            price_source=PriceSource.MARK,
        )

        total_weight = sum(item.data.portfolio_weight for item in assets.items)
        # Allow small floating point tolerance
        assert abs(total_weight - 100.0) < 0.01


class TestAccountEventNormalization:
    """Tests for account event (fill/funding) normalization."""

    def test_normalize_fill_event(self):
        """Test normalizing a trade fill event."""
        from app.providers.backpack import BackpackProvider

        provider = BackpackProvider.__new__(BackpackProvider)

        event, warnings = provider._normalize_fill_event(SAMPLE_FILLS_RESPONSE[0])

        assert event.id == "fill-123"
        assert event.event_type == EventType.TRADE_FILL
        assert event.asset == "USDC"  # feeAsset
        assert event.amount == 1.0  # quantity

    def test_normalize_funding_event(self):
        """Test normalizing a funding event."""
        from app.providers.backpack import BackpackProvider

        provider = BackpackProvider.__new__(BackpackProvider)

        event, warnings = provider._normalize_funding_event(SAMPLE_FUNDING_RESPONSE[0])

        assert event.event_type == EventType.FUNDING_SETTLEMENT
        assert event.amount == -0.05

    def test_event_type_detection(self):
        """Test various event types are correctly detected."""
        from app.providers.backpack import BackpackProvider

        provider = BackpackProvider.__new__(BackpackProvider)

        test_cases = [
            ({"type": "liquidation"}, EventType.LIQUIDATION),
            ({"fillType": "adl"}, EventType.ADL),
            ({"eventType": "funding"}, EventType.FUNDING_SETTLEMENT),
            ({"type": "fee"}, EventType.FEE_CHARGE),
            ({"type": "deposit"}, EventType.DEPOSIT),
            ({"type": "withdraw"}, EventType.WITHDRAWAL),
        ]

        for payload, expected_type in test_cases:
            event, _ = provider._normalize_fill_event(payload)
            assert event.event_type == expected_type


class TestProfileSummaryNormalization:
    """Tests for profile summary normalization."""

    def test_profile_summary_from_account_and_collateral(self):
        """Test profile summary is calculated correctly."""
        from dataclasses import dataclass
        from app.providers.backpack import BackpackProvider
        from app.providers.base import NormalizedList, NormalizedRecord
        from app.schemas import Position

        provider = BackpackProvider.__new__(BackpackProvider)

        # Create mock positions with proper NormalizedRecord
        mock_position = Position(
            symbol="SOL-PERP",
            side="long",
            quantity=10.0,
            entry_price=500.0,
            mark_price=510.0,
            liquidation_price=None,
            unrealized_pnl=100.0,
            margin_used=1000.0,
            opened_at="",
            price_source=PriceSource.MARK,
            exchange_extra={}
        )
        positions = NormalizedList(items=[
            NormalizedRecord(data=mock_position, raw_payload={}, warnings=[])
        ])

        summary = provider._normalize_summary(
            account=SAMPLE_ACCOUNT_RESPONSE,
            collateral_rows=SAMPLE_COLLATERAL_RESPONSE,
            positions=positions,
            price_source=PriceSource.MARK,
        )

        # total_equity = sum of collateral values = 5100 + 4900 = 10000
        assert summary.data.total_equity == 10000.0

        # available_margin = from account.availableMargin (8000.0 in sample)
        # since it's not zero, that's used instead of collateral sum
        assert summary.data.available_margin == 8000.0

        # unrealized_pnl = 100 (from position)
        assert summary.data.unrealized_pnl == 100.0
