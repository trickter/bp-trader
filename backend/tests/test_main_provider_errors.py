from __future__ import annotations

from fastapi.testclient import TestClient

from app.backpack.exceptions import BackpackAuthError, BackpackRequestError
from app.main import app
from app.providers import ProviderError

ADMIN_HEADERS = {"X-Admin-Token": "dev-admin-token"}


class _FailingProvider:
    def __init__(self, error: Exception) -> None:
        self._error = error

    async def fetch_account_snapshot(self, **_: object):
        raise self._error


def test_profile_summary_uses_stable_shape_for_request_errors(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.backpack_mode", "live")
    with TestClient(app) as client:
        client.app.state.backpack_provider = _FailingProvider(
            BackpackRequestError(
                "Backpack request was rejected by the provider.",
                code="backpack_upstream_error",
                status_code=503,
                upstream_status=503,
                retryable=True,
            )
        )
        response = client.get("/api/profile/summary", headers=ADMIN_HEADERS)

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "backpack_upstream_error",
            "message": "Backpack request was rejected by the provider.",
            "provider": "backpack",
            "retryable": True,
            "upstreamStatus": 503,
        }
    }


def test_profile_summary_does_not_expose_raw_upstream_payloads(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.backpack_mode", "live")
    with TestClient(app) as client:
        client.app.state.backpack_provider = _FailingProvider(
            BackpackRequestError(
                "Backpack request was rejected by the provider.",
                code="backpack_upstream_error",
                status_code=502,
                upstream_status=502,
                retryable=True,
            )
        )
        response = client.get("/api/profile/summary", headers=ADMIN_HEADERS)

    detail = response.json()["detail"]
    assert "payload" not in detail
    assert "debug" not in detail


def test_profile_summary_uses_stable_shape_for_auth_errors(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.backpack_mode", "live")
    with TestClient(app) as client:
        client.app.state.backpack_provider = _FailingProvider(
            BackpackAuthError("Signed Backpack requests require api_key and private_key.")
        )
        response = client.get("/api/profile/summary", headers=ADMIN_HEADERS)

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "provider_auth_error",
            "message": "Signed Backpack requests require api_key and private_key.",
            "provider": "backpack",
            "retryable": False,
        }
    }


def test_profile_summary_uses_stable_shape_for_provider_errors(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.backpack_mode", "live")
    with TestClient(app) as client:
        client.app.state.backpack_provider = _FailingProvider(
            ProviderError("Backpack returned an invalid account snapshot.")
        )
        response = client.get("/api/profile/summary", headers=ADMIN_HEADERS)

    assert response.status_code == 502
    assert response.json() == {
        "detail": {
            "code": "provider_response_invalid",
            "message": "Backpack returned an invalid account snapshot.",
            "provider": "backpack",
            "retryable": False,
        }
    }


def test_profile_summary_uses_stable_shape_when_provider_missing(monkeypatch) -> None:
    monkeypatch.setattr("app.main.settings.backpack_mode", "live")
    with TestClient(app) as client:
        client.app.state.backpack_provider = None
        response = client.get("/api/profile/summary", headers=ADMIN_HEADERS)

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "provider_not_initialized",
            "message": "Backpack live provider is not initialized.",
            "provider": "backpack",
            "retryable": True,
        }
    }
