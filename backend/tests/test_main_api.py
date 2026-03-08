from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.mock_data import ASSET_BALANCES, POSITIONS, PROFILE_SUMMARY
from app.providers.base import AccountSnapshot, NormalizedList, NormalizedRecord


class SnapshotCountingProvider:
    def __init__(self) -> None:
        self.snapshot_calls = 0

    async def fetch_account_snapshot(self, price_source):  # noqa: ANN001
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


def test_profile_endpoints_share_short_lived_live_snapshot_cache(monkeypatch) -> None:
    provider = SnapshotCountingProvider()
    monkeypatch.setattr("app.main.settings.backpack_mode", "live")
    monkeypatch.setattr("app.main.settings.admin_api_token", "test-admin-token")

    with TestClient(app) as client:
        client.app.state.backpack_provider = provider

        headers = {"X-Admin-Token": "test-admin-token"}
        summary_response = client.get("/api/profile/summary", headers=headers)
        assets_response = client.get("/api/profile/assets", headers=headers)
        positions_response = client.get("/api/profile/positions", headers=headers)

    assert summary_response.status_code == 200
    assert assets_response.status_code == 200
    assert positions_response.status_code == 200
    assert provider.snapshot_calls == 1
