"""Integration tests for BackpackProvider fetch methods."""
from __future__ import annotations

import asyncio
import time

import pytest

from app.providers.backpack import BackpackProvider
from app.providers.base import (
    AccountSnapshot,
    MarketPulseSnapshot,
    NormalizedList,
    NormalizedRecord,
)
from app.schemas import PriceSource


# Sample API responses
SAMPLE_ACCOUNT = {
    "id": "acc-123",
    "equity": 10000.0,
    "availableMargin": 8000.0,
    "updatedAt": "2024-01-15T10:30:00Z",
}

SAMPLE_CAPITAL = [
    {"asset": "USDC", "available": 5000.0, "locked": 100.0, "usdValue": 5100.0},
]

SAMPLE_COLLATERAL = [
    {"asset": "USDC", "collateralValue": 5100.0, "availableValue": 5000.0},
]

SAMPLE_POSITIONS = [
    {
        "symbol": "SOL-PERP",
        "side": "long",
        "quantity": 10.0,
        "entryPrice": 500.0,
        "markPrice": 510.0,
        "unrealizedPnl": 100.0,
        "marginUsed": 1000.0,
        "openedAt": "2024-01-15T10:00:00Z",
    },
]

SAMPLE_FILLS = [
    {
        "id": "fill-1",
        "symbol": "SOL-PERP",
        "quantity": 1.0,
        "price": 500.0,
        "fee": 0.5,
        "feeAsset": "USDC",
        "timestamp": 1705312800000,
        "fillType": "trade",
    },
]

SAMPLE_FUNDING = [
    {
        "id": "funding-1",
        "symbol": "SOL-PERP",
        "amount": -0.05,
        "asset": "USDC",
        "timestamp": 1705276800000,
    },
]

SAMPLE_MARKET = {
    "symbol": "SOL-PERP",
    "lastPrice": 510.0,
    "markPrice": 509.5,
    "indexPrice": 509.0,
}

SAMPLE_OPEN_INTEREST = {"openInterest": 50000.0}

SAMPLE_FUNDING_RATES = {"fundingRate": 0.0001}

SAMPLE_KLINES = [
    {"timestamp": 1705276800000, "open": 500.0, "high": 510.0, "low": 495.0, "close": 505.0, "volume": 10000.0},
    {"timestamp": 1705277100000, "open": 505.0, "high": 515.0, "low": 500.0, "close": 510.0, "volume": 12000.0},
]


class StubClient:
    """Stub client for testing provider methods."""

    def __init__(self, responses: dict | None = None):
        self._responses = responses or {}
        self.calls = []

    async def get_account(self):
        self.calls.append("get_account")
        return self._responses.get("account", SAMPLE_ACCOUNT)

    async def get_capital(self):
        self.calls.append("get_capital")
        return self._responses.get("capital", SAMPLE_CAPITAL)

    async def get_collateral(self):
        self.calls.append("get_collateral")
        return self._responses.get("collateral", SAMPLE_COLLATERAL)

    async def get_positions(self, symbol=None):
        self.calls.append(f"get_positions({symbol})")
        return self._responses.get("positions", SAMPLE_POSITIONS)

    async def get_fills(self, symbol=None, limit=100, offset=None):
        self.calls.append(f"get_fills({symbol}, {limit})")
        return self._responses.get("fills", SAMPLE_FILLS)

    async def get_funding_history(self, symbol=None, limit=100, offset=None):
        self.calls.append(f"get_funding_history({symbol}, {limit})")
        return self._responses.get("funding", SAMPLE_FUNDING)

    async def get_markets(self):
        self.calls.append("get_markets")
        return []

    async def get_market(self, symbol):
        self.calls.append(f"get_market({symbol})")
        return self._responses.get("market", SAMPLE_MARKET)

    async def get_open_interest(self, symbol):
        self.calls.append(f"get_open_interest({symbol})")
        return self._responses.get("open_interest", SAMPLE_OPEN_INTEREST)

    async def get_funding_rates(self, symbol):
        self.calls.append(f"get_funding_rates({symbol})")
        return self._responses.get("funding_rates", SAMPLE_FUNDING_RATES)

    async def get_klines(self, symbol, interval, start_time, end_time, price_source=None):
        self.calls.append(f"get_klines({symbol}, {interval})")
        return self._responses.get("klines", SAMPLE_KLINES)


class SlowStubClient(StubClient):
    async def get_account(self):
        await asyncio.sleep(0.05)
        return await super().get_account()

    async def get_capital(self):
        await asyncio.sleep(0.05)
        return await super().get_capital()

    async def get_collateral(self):
        await asyncio.sleep(0.05)
        return await super().get_collateral()

    async def get_positions(self, symbol=None):
        await asyncio.sleep(0.05)
        return await super().get_positions(symbol=symbol)


class TestFetchAccountSnapshot:
    """Tests for fetch_account_snapshot method."""

    @pytest.mark.asyncio
    async def test_fetch_account_snapshot_happy_path(self):
        """Test successful account snapshot fetch."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_account_snapshot(price_source=PriceSource.MARK)

        assert isinstance(result, AccountSnapshot)
        assert isinstance(result.summary, NormalizedRecord)
        assert isinstance(result.assets, NormalizedList)
        assert isinstance(result.positions, NormalizedList)

        # Verify all endpoints were called
        assert "get_account" in stub.calls
        assert "get_capital" in stub.calls
        assert "get_collateral" in stub.calls
        assert any("get_positions" in c for c in stub.calls)

    @pytest.mark.asyncio
    async def test_fetch_account_snapshot_with_price_source(self):
        """Test account snapshot respects price source."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        await provider.fetch_account_snapshot(price_source=PriceSource.INDEX)

        # Verify price source was used (check summary data)
        result = await provider.fetch_account_snapshot(price_source=PriceSource.INDEX)
        assert result.summary.data.price_source == PriceSource.INDEX

    @pytest.mark.asyncio
    async def test_fetch_account_snapshot_runs_upstream_calls_concurrently(self):
        stub = SlowStubClient()
        provider = BackpackProvider(client=stub)

        started_at = time.perf_counter()
        await provider.fetch_account_snapshot(price_source=PriceSource.MARK)
        elapsed = time.perf_counter() - started_at

        assert elapsed < 0.15


class TestFetchAccountEvents:
    """Tests for fetch_account_events method."""

    @pytest.mark.asyncio
    async def test_fetch_account_events_happy_path(self):
        """Test successful account events fetch."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_account_events(symbol="SOL-PERP", limit=50)

        assert isinstance(result, NormalizedList)
        assert len(result.items) > 0

        # Should have fills
        fill_items = [item for item in result.items if "fill" in item.data.id.lower()]
        assert len(fill_items) > 0

    @pytest.mark.asyncio
    async def test_fetch_account_events_with_symbol_filter(self):
        """Test events can be filtered by symbol."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        await provider.fetch_account_events(symbol="SOL-PERP")

        assert "get_fills(SOL-PERP" in stub.calls[0]


class TestFetchMarketPulse:
    """Tests for fetch_market_pulse method."""

    @pytest.mark.asyncio
    async def test_fetch_market_pulse_happy_path(self):
        """Test successful market pulse fetch."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_market_pulse(
            symbol="SOL-PERP",
            interval="1m",
            start_time=1705276800000,
            end_time=1705277100000,
            price_source=PriceSource.MARK,
        )

        assert isinstance(result, MarketPulseSnapshot)
        assert isinstance(result.metrics, NormalizedList)
        assert len(result.metrics.items) > 0

    @pytest.mark.asyncio
    async def test_fetch_market_pulse_includes_price_metrics(self):
        """Test market pulse includes price metrics."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_market_pulse(
            symbol="SOL-PERP",
            interval="1m",
            start_time=1705276800000,
            end_time=1705277100000,
            price_source=PriceSource.MARK,
        )

        # Check for price metrics
        metric_labels = [item.data.label for item in result.metrics.items]
        assert any("price" in label.lower() for label in metric_labels)

    @pytest.mark.asyncio
    async def test_fetch_market_pulse_skips_klines_when_not_requested(self):
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_market_pulse(
            symbol="SOL-PERP",
            price_source=PriceSource.MARK,
        )

        assert isinstance(result, MarketPulseSnapshot)
        assert not any(call.startswith("get_klines") for call in stub.calls)

    @pytest.mark.asyncio
    async def test_fetch_market_pulse_can_include_klines_explicitly(self):
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_market_pulse(
            symbol="SOL-PERP",
            interval="1m",
            start_time=1705276800000,
            end_time=1705277100000,
            price_source=PriceSource.MARK,
            include_klines=True,
        )

        assert any(call.startswith("get_klines") for call in stub.calls)


class TestFetchExchangeAccounts:
    """Tests for fetch_exchange_accounts method."""

    @pytest.mark.asyncio
    async def test_fetch_exchange_accounts_happy_path(self):
        """Test successful exchange accounts fetch."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_exchange_accounts()

        assert isinstance(result, NormalizedList)
        assert len(result.items) > 0


class TestFetchKlines:
    """Tests for fetch_klines method."""

    @pytest.mark.asyncio
    async def test_fetch_klines_happy_path(self):
        """Test successful klines fetch."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_klines(
            symbol="SOL-PERP",
            interval="1m",
            start_time=1705276800000,
            end_time=1705277100000,
            price_source=PriceSource.MARK,
        )

        assert isinstance(result, NormalizedRecord)
        assert len(result.data.candles) > 0

    @pytest.mark.asyncio
    async def test_fetch_klines_candle_structure(self):
        """Test klines have correct candle structure."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_klines(
            symbol="SOL-PERP",
            interval="1m",
            start_time=1705276800000,
            end_time=1705277100000,
            price_source=PriceSource.MARK,
        )

        candle = result.data.candles[0]
        assert hasattr(candle, "timestamp")
        assert hasattr(candle, "open")
        assert hasattr(candle, "high")
        assert hasattr(candle, "low")
        assert hasattr(candle, "close")
        assert hasattr(candle, "volume")


class TestProviderWithEmptyResponses:
    """Tests for provider behavior with empty responses."""

    @pytest.mark.asyncio
    async def test_empty_positions(self):
        """Test provider handles empty positions."""
        stub = StubClient({"positions": []})
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_account_snapshot()

        assert len(result.positions.items) == 0

    @pytest.mark.asyncio
    async def test_empty_assets(self):
        """Test provider handles empty assets."""
        stub = StubClient({"capital": [], "collateral": []})
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_account_snapshot()

        # Should still return, possibly with warnings
        assert isinstance(result, AccountSnapshot)


class TestProviderWarnings:
    """Tests for provider warning generation."""

    @pytest.mark.asyncio
    async def test_no_warnings_on_valid_data(self):
        """Test no warnings with valid data."""
        stub = StubClient()
        provider = BackpackProvider(client=stub)

        result = await provider.fetch_account_snapshot()

        # Valid data should have no warnings
        assert len(result.assets.warnings) == 0
        assert len(result.positions.warnings) == 0
