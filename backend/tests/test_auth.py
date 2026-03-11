"""Tests for auth.py - Authentication module."""
from __future__ import annotations

import asyncio
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import config as config_module
from app import main as main_module
from app.auth import require_admin_api_token


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
            asyncio.run(require_admin_api_token("test-admin-token"))

    def test_missing_token_raises_401(self, monkeypatch) -> None:
        """Test that missing token raises 401."""
        monkeypatch.setenv("APP_ENV", "test")
        monkeypatch.setenv("ALLOW_INSECURE_DEV_DEFAULTS", "true")
        monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")

        importlib = pytest.importorskip("importlib")
        importlib.reload(config_module)

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(require_admin_api_token(None))

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
            asyncio.run(require_admin_api_token("invalid-token"))

        assert exc_info.value.status_code == 403
        assert "Invalid admin API token" in exc_info.value.detail


class TestApiAuthentication:
    """Tests for API endpoint authentication."""

    def test_healthz_does_not_require_auth(self) -> None:
        """Test that healthz endpoint does not require auth."""
        # Use existing app that has services initialized
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/healthz")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    def test_api_endpoints_require_auth(self) -> None:
        """Test that API endpoints require authentication."""
        from app.main import app

        with TestClient(app) as client:
            # Try to access API endpoint without auth
            response = client.get("/api/profile/summary")
            assert response.status_code in (401, 403)

    def test_api_endpoints_accept_valid_token(self) -> None:
        """Test that API endpoints accept valid token."""
        from app.main import app
        from app import config as cfg

        with TestClient(app) as client:
            headers = {"X-Admin-Token": cfg.settings.admin_api_token}
            response = client.get("/api/profile/summary", headers=headers)
            assert response.status_code == 200
