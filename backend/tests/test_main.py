"""Tests for main.py - FastAPI application entry point."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import config as config_module
from app import main as main_module


@pytest.fixture
def client(monkeypatch) -> TestClient:
    """Create a test client with mocked settings."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("ALLOW_INSECURE_DEV_DEFAULTS", "true")
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    monkeypatch.setenv("BACKPACK_MODE", "mock")

    importlib = pytest.importorskip("importlib")
    importlib.reload(config_module)
    reloaded_main = importlib.reload(main_module)

    return TestClient(reloaded_main.app)


def test_healthcheck_returns_ok(client: TestClient) -> None:
    """Test that healthz endpoint returns OK status."""
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backpack-quant-console-api"


def test_healthcheck_includes_environment(client: TestClient) -> None:
    """Test that healthz includes environment info."""
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "backpackMode" in data


def test_app_has_cors_middleware(client: TestClient) -> None:
    """Test that CORS middleware is properly configured."""
    response = client.options(
        "/healthz",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 200
