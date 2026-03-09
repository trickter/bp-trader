"""Tests for auth.py - Authentication module."""
from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import config as config_module
from app import main as main_module
from app.auth import require_admin_api_token


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


class TestRequireAdminApiToken:
    """Tests for require_admin_api_token function."""

    def test_valid_token_passes(self, monkeypatch) -> None:
        """Test that a valid admin token passes validation."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("ALLOW_INSECURE_DEV_DEFAULTS", "true")
        monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")

        importlib = pytest.importorskip("importlib")
        importlib.reload(config_module)

        # Valid token should not raise
        with patch.object(config_module.settings, "admin_api_token", "test-admin-token"):
            # Should not raise
            import asyncio
            asyncio.get_event_loop().run_until_complete(require_admin_api_token("test-admin-token"))

    def test_missing_token_raises_401(self, monkeypatch) -> None:
        """Test that missing token raises 401."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("ALLOW_INSECURE_DEV_DEFAULTS", "true")
        monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")

        importlib = pytest.importorskip("importlib")
        importlib.reload(config_module)

        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.get_event_loop().run_until_complete(require_admin_api_token(None))

        assert exc_info.value.status_code == 401
        assert "Missing X-Admin-Token" in exc_info.value.detail

    def test_invalid_token_raises_403(self, monkeypatch) -> None:
        """Test that invalid token raises 403."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("ALLOW_INSECURE_DEV_DEFAULTS", "true")
        monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")

        importlib = pytest.importorskip("importlib")
        importlib.reload(config_module)

        with pytest.raises(HTTPException) as exc_info:
            import asyncio
            asyncio.get_event_loop().run_until_complete(require_admin_api_token("invalid-token"))

        assert exc_info.value.status_code == 403
        assert "Invalid admin API token" in exc_info.value.detail


class TestApiAuthentication:
    """Tests for API endpoint authentication."""

    def test_api_endpoints_require_auth(self, client: TestClient) -> None:
        """Test that API endpoints require authentication."""
        # Try to access API endpoint without auth
        response = client.get("/api/profile/summary")
        assert response.status_code in (401, 403)

    def test_api_endpoints_accept_valid_token(self, client: TestClient) -> None:
        """Test that API endpoints accept valid token."""
        headers = {"X-Admin-Token": "test-admin-token"}
        response = client.get("/api/profile/summary", headers=headers)
        assert response.status_code == 200

    def test_healthz_does_not_require_auth(self, client: TestClient) -> None:
        """Test that healthz endpoint does not require auth."""
        response = client.get("/healthz")
        assert response.status_code == 200
