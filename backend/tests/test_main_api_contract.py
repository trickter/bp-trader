from __future__ import annotations

import importlib

from fastapi.testclient import TestClient

import app.config as config_module
import app.main as main_module
from app.mock_data import ASSET_BALANCES, POSITIONS, PROFILE_SUMMARY
from app.providers.base import AccountSnapshot, NormalizedList, NormalizedRecord
from app.schemas import PriceSource


def create_client(monkeypatch) -> tuple[TestClient, object]:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_INSECURE_DEV_DEFAULTS", "true")
    monkeypatch.setenv("ADMIN_API_TOKEN", "dev-admin-token")
    monkeypatch.setenv("BACKPACK_MODE", "mock")
    importlib.reload(config_module)
    reloaded_main = importlib.reload(main_module)
    client = TestClient(reloaded_main.app)
    return client, reloaded_main


def admin_headers() -> dict[str, str]:
    return {"X-Admin-Token": "dev-admin-token"}


def test_template_backtest_contract_is_two_step(monkeypatch):
    client, _ = create_client(monkeypatch)

    with client:
        create_response = client.post(
            "/api/strategies/templates/strat_001/backtests",
            headers=admin_headers(),
            json={
                "symbol": "BTC_USDC_PERP",
                "interval": "1d",
                "startTime": 1740787200,
                "endTime": 1741305600,
                "priceSource": "last",
                "feeBps": 2,
                "slippageBps": 4,
            },
        )

        assert create_response.status_code == 200
        accepted = create_response.json()
        assert accepted["status"] == "completed"
        assert accepted["resultPath"].startswith("/api/backtests/")

        result_response = client.get(accepted["resultPath"], headers=admin_headers())
        assert result_response.status_code == 200
        result = result_response.json()
        assert result["id"] == accepted["id"]
        assert result["symbol"] == "BTC_USDC_PERP"
        assert result["priceSource"] == "last"


def test_agent_context_exposes_capability_discovery(monkeypatch):
    client, _ = create_client(monkeypatch)

    with client:
        response = client.get("/api/agent/context", headers=admin_headers())

        assert response.status_code == 200
        payload = response.json()
        assert payload["accountMode"] == "mock"
        assert "profile.summary.read" in payload["availableCapabilities"]
        assert payload["resources"]["profileSummary"] == "/api/profile/summary"


def test_live_profile_routes_share_snapshot_cache(monkeypatch):
    client, reloaded_main = create_client(monkeypatch)
    stub_provider = SnapshotCountingProvider()

    with client:
        reloaded_main.settings.backpack_mode = "live"
        reloaded_main.app.state.backpack_provider = stub_provider

        summary = client.get("/api/profile/summary", headers=admin_headers())
        assets = client.get("/api/profile/assets", headers=admin_headers())
        positions = client.get("/api/profile/positions", headers=admin_headers())

        assert summary.status_code == 200
        assert assets.status_code == 200
        assert positions.status_code == 200
        assert stub_provider.snapshot_calls == 1

        reloaded_main.settings.backpack_mode = "mock"


class SnapshotCountingProvider:
    def __init__(self) -> None:
        self.snapshot_calls = 0

    async def fetch_account_snapshot(self, price_source: PriceSource):
        self.snapshot_calls += 1
        return AccountSnapshot(
            summary=NormalizedRecord(data=PROFILE_SUMMARY, raw_payload=PROFILE_SUMMARY.model_dump(by_alias=True)),
            assets=NormalizedList(
                items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in ASSET_BALANCES]
            ),
            positions=NormalizedList(
                items=[NormalizedRecord(data=item, raw_payload=item.model_dump(by_alias=True)) for item in POSITIONS]
            ),
        )
