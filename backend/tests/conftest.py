"""Shared fixtures for backend tests."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.backpack.types import BackpackAuthConfig


# Sample Ed25519 private key (32-byte seed) for testing
# This is a randomly generated test key - NEVER use in production
TEST_PRIVATE_KEY_HEX = "653b6763d073ee4edaefdf9012cc969c96cd9d4aa957fc59c50c9a4f4bda2f1c"


@pytest.fixture
def test_auth_config() -> BackpackAuthConfig:
    """Basic test auth config."""
    return BackpackAuthConfig(
        api_key="test_api_key",
        private_key=TEST_PRIVATE_KEY_HEX,
        window_ms=5000,
    )


@pytest.fixture
def mock_http_response():
    """Factory for mock HTTP responses."""
    def _create(status_code: int = 200, json_data: dict | list | None = None):
        response = MagicMock()
        response.status_code = status_code
        if json_data is not None:
            response.json.return_value = json_data
            response.text = str(json_data)
        else:
            response.json.side_effect = ValueError("No JSON")
            response.text = ""
        return response
    return _create


# Sample Backpack API responses for testing

SAMPLE_ACCOUNT_RESPONSE = {
    "id": "test-account-123",
    "accountId": "test-account-123",
    "equity": 10000.0,
    "availableMargin": 8000.0,
    "realizedPnl24h": 150.5,
    "winRate": 0.65,
    "updatedAt": "2024-01-15T10:30:00Z",
}

SAMPLE_CAPITAL_RESPONSE = [
    {"asset": "USDC", "available": 5000.0, "locked": 100.0, "usdValue": 5100.0},
    {"asset": "SOL", "available": 10.0, "locked": 2.0, "usdValue": 4900.0},
]

SAMPLE_COLLATERAL_RESPONSE = [
    {"asset": "USDC", "collateralValue": 5100.0, "availableValue": 5000.0},
    {"asset": "SOL", "collateralValue": 4900.0, "availableValue": 4800.0},
]

SAMPLE_POSITIONS_RESPONSE = [
    {
        "symbol": "SOL-PERP",
        "side": "long",
        "quantity": 10.0,
        "entryPrice": 490.0,
        "markPrice": 495.0,
        "unrealizedPnl": 50.0,
        "marginUsed": 1000.0,
        "openedAt": "2024-01-10T08:00:00Z",
    },
    {
        "symbol": "BTC-PERP",
        "side": "short",
        "quantity": -0.5,
        "entryPrice": 42000.0,
        "markPrice": 41800.0,
        "unrealizedPnl": 100.0,
        "marginUsed": 2000.0,
        "openedAt": "2024-01-12T12:00:00Z",
    },
]

SAMPLE_FILLS_RESPONSE = [
    {
        "id": "fill-123",
        "symbol": "SOL-PERP",
        "side": "buy",
        "quantity": 1.0,
        "price": 490.0,
        "fee": 0.49,
        "feeAsset": "USDC",
        "timestamp": 1705312800000,
        "fillType": "trade",
    },
    {
        "id": "fill-124",
        "symbol": "BTC-PERP",
        "side": "sell",
        "quantity": 0.1,
        "price": 42000.0,
        "fee": 4.2,
        "feeAsset": "USDC",
        "timestamp": 1705226400000,
        "fillType": "trade",
    },
]

SAMPLE_FUNDING_RESPONSE = [
    {
        "id": "funding-001",
        "symbol": "SOL-PERP",
        "amount": -0.05,
        "asset": "USDC",
        "timestamp": 1705276800000,
    },
]

SAMPLE_MARKET_RESPONSE = {
    "symbol": "SOL-PERP",
    "lastPrice": 495.0,
    "markPrice": 494.5,
    "indexPrice": 494.0,
}

SAMPLE_KLINES_RESPONSE = [
    ["1705276800000", "490.0", "495.0", "488.0", "492.0", "10000.0"],
    ["1705277100000", "492.0", "498.0", "491.0", "496.0", "15000.0"],
    ["1705277400000", "496.0", "500.0", "494.0", "498.0", "12000.0"],
]
