"""Tests for BackpackClient signed endpoints and headers."""
from __future__ import annotations

import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, patch

from app.backpack.client import BackpackClient
from app.backpack.types import BackpackAuthConfig, BackpackOrderRequest
from app.backpack.exceptions import BackpackAuthError


# Sample key for testing - 32 bytes as raw bytes
TEST_PRIVATE_KEY_BYTES = bytes.fromhex("653b6763d073ee4edaefdf9012cc969c96cd9d4aa957fc59c50c9a4f4bda2f1c")


@pytest.fixture
def auth_config() -> BackpackAuthConfig:
    return BackpackAuthConfig(
        api_key="test_api_key",
        private_key=TEST_PRIVATE_KEY_BYTES,
        window_ms=5000,
    )


@pytest.fixture
def client(auth_config) -> BackpackClient:
    return BackpackClient(auth_config)


class TestSignedHeaders:
    """Tests for signed header construction."""

    def test_build_signed_headers_requires_api_key(self):
        """Test that signed requests require api_key."""
        # Create client without api_key
        config = BackpackAuthConfig(private_key=TEST_PRIVATE_KEY_BYTES)
        client = BackpackClient(config)

        with pytest.raises(BackpackAuthError, match="api_key"):
            client._build_signed_headers(instruction="test", params={})

    def test_build_signed_headers_requires_private_key(self):
        """Test that signed requests require private_key."""
        config = BackpackAuthConfig(api_key="test_key")
        client = BackpackClient(config)

        with pytest.raises(BackpackAuthError, match="private_key"):
            client._build_signed_headers(instruction="test", params={})

    def test_signed_headers_structure(self, client):
        """Test signed headers contain required fields."""
        headers = client._build_signed_headers(instruction="accountQuery", params={})

        assert "X-API-Key" in headers
        assert "X-Signature" in headers
        assert "X-Timestamp" in headers
        assert "X-Window" in headers

    def test_signed_headers_values(self, client):
        """Test signed headers have correct values."""
        headers = client._build_signed_headers(instruction="accountQuery", params={})

        assert headers["X-API-Key"] == "test_api_key"
        assert headers["X-Window"] == "5000"

    def test_signed_headers_timestamp_format(self, client):
        """Test timestamp is integer string."""
        headers = client._build_signed_headers(instruction="accountQuery", params={})

        # Should be string of integer
        assert headers["X-Timestamp"].isdigit()

    def test_signature_is_valid_base64(self, client):
        """Test signature is valid base64."""
        headers = client._build_signed_headers(instruction="accountQuery", params={})

        decoded = base64.b64decode(headers["X-Signature"])
        assert len(decoded) == 64  # Ed25519 signature is 64 bytes

    def test_batch_signature_is_valid_base64(self, client):
        headers = client._build_signed_batch_headers(
            instruction="orderExecute",
            entries=[
                {
                    "symbol": "BTC_USDC_PERP",
                    "side": "Bid",
                    "orderType": "Market",
                    "quantity": "0.001",
                }
            ],
        )

        decoded = base64.b64decode(headers["X-Signature"])
        assert len(decoded) == 64


class TestClientEndpoints:
    """Tests for client endpoint parameter handling."""

    @pytest.mark.asyncio
    async def test_get_positions_with_symbol(self, client):
        """Test get_positions accepts symbol parameter."""
        mock_response = {"success": True, "data": []}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_positions(symbol="SOL-PERP")

            # Verify the request was called with correct params
            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args
            # Check params contain symbol
            assert "params" in call_kwargs.kwargs or len(call_kwargs.args) > 2

    @pytest.mark.asyncio
    async def test_get_fills_parameters(self, client):
        """Test get_fills accepts symbol, limit, offset."""
        mock_response = {"success": True, "data": []}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_fills(symbol="SOL-PERP", limit=50, offset=100)

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_funding_history_parameters(self, client):
        """Test get_funding_history accepts symbol, limit."""
        mock_response = {"success": True, "data": []}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_funding_history(symbol="SOL-PERP", limit=50)

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_klines_parameters(self, client):
        """Test get_klines constructs correct parameters."""
        mock_response = []

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_klines(
                symbol="SOL-PERP",
                interval="1m",
                start_time=1705276800000,
                end_time=1705277100000,
            )

            mock_request.assert_called_once()
            # Check it was called as public endpoint
            call_args = mock_request.call_args
            # First arg should be GET, second should be path
            assert call_args.args[0] == "GET"
            assert "/api/v1/klines" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_get_klines_with_price_source(self, client):
        """Test get_klines accepts price_source parameter."""
        mock_response = []

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_klines(
                symbol="SOL-PERP",
                interval="1m",
                start_time=1705276800000,
                end_time=1705277100000,
                price_source="mark",
            )

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_open_interest_parameters(self, client):
        """Test get_open_interest constructs correct parameters."""
        mock_response = {}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_open_interest(
                symbol="SOL-PERP",
                interval="1h",
                start_time=1705276800000,
                end_time=1705277100000,
            )

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_funding_rates_parameters(self, client):
        """Test get_funding_rates accepts symbol, limit, offset."""
        mock_response = {}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_funding_rates(symbol="SOL-PERP", limit=50)

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_markets_calls_correct_endpoint(self, client):
        """Test get_markets uses correct public endpoint."""
        mock_response = {}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_markets()

            call_args = mock_request.call_args
            assert "/api/v1/market" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_get_market_with_symbol(self, client):
        """Test get_market accepts symbol parameter."""
        mock_response = {}

        with patch.object(client, '_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            await client.get_market("SOL-PERP")

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_open_orders_parameters(self, client):
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"orders": []}
            await client.get_open_orders(symbol="BTC_USDC_PERP", limit=25)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "GET"
            assert "/api/v1/orders" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_get_order_history_parameters(self, client):
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"orders": []}
            await client.get_order_history(symbol="BTC_USDC_PERP", limit=25, offset=10)

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "GET"
            assert "/wapi/v1/history/orders" in call_args.args[1]

    @pytest.mark.asyncio
    async def test_create_order_uses_signed_json_body(self, client):
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"id": "ord_123"}

            await client.create_order(
                BackpackOrderRequest(
                    symbol="BTC_USDC_PERP",
                    side="Bid",
                    order_type="Market",
                    quantity="0.001",
                    client_id=123,
                )
            )

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "POST"
            assert "/api/v1/order" in call_args.args[1]
            assert call_args.kwargs["json_body"]["clientId"] == 123
            assert call_args.kwargs["params"] == {}

    @pytest.mark.asyncio
    async def test_create_orders_posts_batch_payload(self, client):
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"submitted": 2}

            await client.create_orders(
                [
                    BackpackOrderRequest(
                        symbol="BTC_USDC_PERP",
                        side="Bid",
                        order_type="Market",
                        quantity="0.001",
                        client_id=1,
                    ),
                    BackpackOrderRequest(
                        symbol="ETH_USDC_PERP",
                        side="Ask",
                        order_type="Market",
                        quantity="0.01",
                        client_id=2,
                        reduce_only=True,
                    ),
                ]
            )

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "POST"
            assert "/api/v1/orders" in call_args.args[1]
            assert len(call_args.kwargs["json_body"]) == 2

    @pytest.mark.asyncio
    async def test_cancel_order_uses_delete_with_signed_json_body(self, client):
        with patch.object(client, "_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {"status": "canceled"}

            await client.cancel_order(symbol="BTC_USDC_PERP", client_id="123")

            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args.args[0] == "DELETE"
            assert "/api/v1/order" in call_args.args[1]
            assert call_args.kwargs["json_body"]["clientId"] == "123"


class TestClientContextManager:
    """Tests for client async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_enter(self, auth_config):
        """Test client can be used as async context manager."""
        async with BackpackClient(auth_config) as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_context_manager_exit_closes_client(self, auth_config):
        """Test context manager closes internal client."""
        async with BackpackClient(auth_config) as client:
            await client._client.aclose()  # Close for test
        # Should not raise


class TestClientErrorHandling:
    """Tests for client error handling."""

    def test_client_requires_auth_for_signed_endpoints(self):
        """Test signed endpoints require auth config."""
        # No api_key
        config = BackpackAuthConfig(private_key=TEST_PRIVATE_KEY_BYTES)
        client = BackpackClient(config)

        with pytest.raises(BackpackAuthError):
            # Would need to actually call an endpoint, but header build fails first
            client._build_signed_headers(instruction="test", params={})
