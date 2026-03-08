from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_healthz_remains_public():
    client = TestClient(app)

    response = client.get("/healthz")

    assert response.status_code == 200


def test_api_rejects_missing_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_token", "test-admin-token")
    client = TestClient(app)

    response = client.get("/api/profile/summary")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing X-Admin-Token header."}


def test_api_rejects_invalid_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_token", "test-admin-token")
    client = TestClient(app)

    response = client.get("/api/profile/summary", headers={"X-Admin-Token": "wrong-token"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid admin API token."}


def test_api_accepts_valid_admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_api_token", "test-admin-token")
    client = TestClient(app)

    response = client.get("/api/profile/summary", headers={"X-Admin-Token": "test-admin-token"})

    assert response.status_code == 200
    assert response.json()["priceSource"] == "mark"
