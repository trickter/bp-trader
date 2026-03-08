from __future__ import annotations

import pytest

from app.config import Settings


def test_allows_explicit_local_dev_defaults() -> None:
    settings = Settings(
        _env_file=None,
        app_env="development",
        allow_insecure_dev_defaults=True,
        admin_api_token="dev-admin-token",
        database_url="postgresql://postgres:postgres@localhost:5432/trader",
    )

    assert settings.allow_insecure_dev_defaults is True


def test_rejects_weak_admin_token_outside_explicit_local_dev() -> None:
    with pytest.raises(ValueError, match="ADMIN_API_TOKEN"):
        Settings(
            _env_file=None,
            app_env="production",
            allow_insecure_dev_defaults=False,
            admin_api_token="dev-admin-token",
            database_url="postgresql://user:strong-password@db:5432/trader",
        )


def test_rejects_default_database_credentials_outside_explicit_local_dev() -> None:
    with pytest.raises(ValueError, match="DATABASE_URL"):
        Settings(
            _env_file=None,
            app_env="production",
            allow_insecure_dev_defaults=False,
            admin_api_token="prod-admin-token",
            database_url="postgresql://postgres:postgres@db:5432/trader",
        )


def test_live_mode_requires_backpack_credentials() -> None:
    with pytest.raises(ValueError, match="BACKPACK_MODE=live"):
        Settings(
            _env_file=None,
            app_env="production",
            allow_insecure_dev_defaults=False,
            admin_api_token="prod-admin-token",
            database_url="postgresql://user:strong-password@db:5432/trader",
            backpack_mode="live",
        )
