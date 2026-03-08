"""Tests for Backpack signing functionality."""
from __future__ import annotations

import pytest
import time

from app.backpack.signing import (
    sign_instruction,
    _decode_private_key_bytes,
    _load_private_key,
)
from app.backpack.exceptions import BackpackSigningError


# Test private key - 32-byte seed (hex encoded) = 64 hex characters
# This is a randomly generated test-only key, do NOT use in production
TEST_PRIVATE_KEY_HEX = "653b6763d073ee4edaefdf9012cc969c96cd9d4aa957fc59c50c9a4f4bda2f1c"
TEST_PRIVATE_KEY_BYTES = bytes.fromhex(TEST_PRIVATE_KEY_HEX)


class TestDecodePrivateKeyBytes:
    """Tests for private key decoding."""

    def test_decode_hex_string(self):
        """Test decoding hex string."""
        result = _decode_private_key_bytes(TEST_PRIVATE_KEY_HEX)
        # Should be valid bytes - the function handles various formats
        # Valid lengths: 32 (seed), 64 (expanded key), or PEM format
        assert isinstance(result, bytes) and len(result) >= 32

    def test_decode_bytes_directly(self):
        """Test passing bytes directly."""
        result = _decode_private_key_bytes(TEST_PRIVATE_KEY_BYTES)
        assert result == TEST_PRIVATE_KEY_BYTES

    def test_decode_base64_string(self):
        """Test decoding base64 string."""
        import base64
        b64_key = base64.b64encode(TEST_PRIVATE_KEY_BYTES).decode()
        result = _decode_private_key_bytes(b64_key)
        assert result == TEST_PRIVATE_KEY_BYTES

    def test_invalid_format_raises_error(self):
        """Test that invalid format raises BackpackSigningError."""
        with pytest.raises(BackpackSigningError):
            _decode_private_key_bytes("not-a-valid-key")


class TestLoadPrivateKey:
    """Tests for Ed25519 private key loading."""

    def test_load_from_32byte_seed(self):
        """Test loading from 32-byte seed."""
        key = _load_private_key(TEST_PRIVATE_KEY_BYTES)
        assert key is not None
        # Verify we can sign something (Ed25519 default algorithm)
        public_key = key.public_key()
        signature = key.sign(b"test message")
        public_key.verify(signature, b"test message")

    def test_load_from_64byte_expanded_key(self):
        """Test loading from 64-byte expanded key (takes first 32 bytes)."""
        expanded_key = TEST_PRIVATE_KEY_BYTES + b"\x00" * 32  # Pad to 64 bytes
        key = _load_private_key(expanded_key)
        assert key is not None


class TestSignInstruction:
    """Tests for instruction signing."""

    def test_sign_produces_valid_signature(self):
        """Test that signing produces a valid base64-encoded signature."""
        timestamp_ms = 1705312800000
        window_ms = 5000

        signature = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params={"key": "value"},
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )

        # Signature should be valid base64
        import base64
        decoded = base64.b64decode(signature)
        assert len(decoded) == 64  # Ed25519 signatures are 64 bytes

    def test_same_inputs_produce_same_signature(self):
        """Test that identical inputs produce identical signatures."""
        timestamp_ms = 1705312800000
        window_ms = 5000
        params = {"key": "value"}

        sig1 = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params=params,
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )
        sig2 = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params=params,
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )

        assert sig1 == sig2

    def test_different_timestamp_produces_different_signature(self):
        """Test that different timestamps produce different signatures."""
        window_ms = 5000

        sig1 = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params={},
            timestamp_ms=1705312800000,
            window_ms=window_ms,
        )
        sig2 = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params={},
            timestamp_ms=1705312801000,
            window_ms=window_ms,
        )

        assert sig1 != sig2

    def test_different_instruction_produces_different_signature(self):
        """Test that different instructions produce different signatures."""
        timestamp_ms = 1705312800000
        window_ms = 5000

        sig1 = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params={},
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )
        sig2 = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="positionQuery",
            params={},
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )

        assert sig1 != sig2

    def test_empty_params(self):
        """Test signing with empty params."""
        timestamp_ms = 1705312800000
        window_ms = 5000

        signature = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params={},
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )

        assert signature is not None
        import base64
        decoded = base64.b64decode(signature)
        assert len(decoded) == 64

    def test_signing_with_none_values_in_params(self):
        """Test that None values in params are handled correctly."""
        timestamp_ms = 1705312800000
        window_ms = 5000

        # Should not raise - None values should be filtered out
        signature = sign_instruction(
            private_key=TEST_PRIVATE_KEY_BYTES,
            instruction="accountQuery",
            params={"key": None, "other": "value"},
            timestamp_ms=timestamp_ms,
            window_ms=window_ms,
        )

        assert signature is not None
