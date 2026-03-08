"""Tests for Backpack serialization functionality."""
from __future__ import annotations

import pytest
from app.backpack.serialize import (
    serialize_scalar,
    canonical_query_string,
    signature_payload,
)


class TestSerializeScalar:
    """Tests for scalar value serialization."""

    def test_serialize_none(self):
        """Test serializing None returns empty string."""
        assert serialize_scalar(None) == ""

    def test_serialize_bool_true(self):
        """Test serializing True returns 'true'."""
        assert serialize_scalar(True) == "true"

    def test_serialize_bool_false(self):
        """Test serializing False returns 'false'."""
        assert serialize_scalar(False) == "false"

    def test_serialize_int(self):
        """Test serializing integer."""
        assert serialize_scalar(123) == "123"

    def test_serialize_float(self):
        """Test serializing float."""
        assert serialize_scalar(123.45) == "123.45"

    def test_serialize_string(self):
        """Test serializing string."""
        assert serialize_scalar("hello") == "hello"

    def test_serialize_list(self):
        """Test serializing list produces JSON."""
        result = serialize_scalar([1, 2, 3])
        assert result == "[1,2,3]"

    def test_serialize_dict(self):
        """Test serializing dict produces sorted JSON."""
        result = serialize_scalar({"b": 2, "a": 1})
        assert result == '{"a":1,"b":2}'  # Sorted keys

    def test_serialize_list_with_strings(self):
        """Test serializing list with strings."""
        result = serialize_scalar(["a", "b"])
        assert result == '["a","b"]'


class TestCanonicalQueryString:
    """Tests for canonical query string generation."""

    def test_empty_params(self):
        """Test empty params returns empty string."""
        assert canonical_query_string({}) == ""

    def test_single_param(self):
        """Test single parameter."""
        assert canonical_query_string({"key": "value"}) == "key=value"

    def test_multiple_params_sorted(self):
        """Test multiple params are sorted alphabetically."""
        result = canonical_query_string({"z": "1", "a": "2", "m": "3"})
        assert result == "a=2&m=3&z=1"

    def test_none_values_filtered(self):
        """Test that None values are filtered out."""
        result = canonical_query_string({"a": "1", "b": None, "c": "2"})
        assert result == "a=1&c=2"

    def test_special_characters_encoded(self):
        """Test special characters are URL encoded."""
        result = canonical_query_string({"key": "value with spaces"})
        assert "key=value%20with%20spaces" == result

    def test_numbers_preserved(self):
        """Test numeric values are preserved as strings."""
        result = canonical_query_string({"count": 42, "price": 99.99})
        assert result == "count=42&price=99.99"

    def test_bool_values_serialized(self):
        """Test boolean values are serialized."""
        result = canonical_query_string({"active": True, "deleted": False})
        # Should be sorted alphabetically with serialized bools
        assert "active=true" in result
        assert "deleted=false" in result


class TestSignaturePayload:
    """Tests for signature payload generation."""

    def test_basic_payload(self):
        """Test basic payload generation."""
        result = signature_payload(
            instruction="accountQuery",
            params={},
            timestamp_ms=1705312800000,
            window_ms=5000,
        )
        assert "instruction=accountQuery" in result
        assert "timestamp=1705312800000" in result
        assert "window=5000" in result

    def test_payload_with_params(self):
        """Test payload includes params."""
        result = signature_payload(
            instruction="accountQuery",
            params={"key": "value"},
            timestamp_ms=1705312800000,
            window_ms=5000,
        )
        assert "key=value" in result

    def test_payload_order(self):
        """Test payload components order is correct."""
        result = signature_payload(
            instruction="positionQuery",
            params={"symbol": "SOL-PERP"},
            timestamp_ms=1705312800000,
            window_ms=5000,
        )
        # Order: instruction, params (if any), timestamp, window
        parts = result.split("&")
        assert parts[0] == "instruction=positionQuery"
        assert "symbol=SOL-PERP" in parts
        assert "timestamp=1705312800000" in parts
        assert "window=5000" in parts

    def test_payload_timestamp_format(self):
        """Test timestamp is included as integer string."""
        result = signature_payload(
            instruction="test",
            params={},
            timestamp_ms=1705312800000,
            window_ms=5000,
        )
        # Should be exact integer, not formatted
        assert "timestamp=1705312800000" in result

    def test_payload_window_format(self):
        """Test window is included as integer string."""
        result = signature_payload(
            instruction="test",
            params={},
            timestamp_ms=1705312800000,
            window_ms=10000,
        )
        assert "window=10000" in result
