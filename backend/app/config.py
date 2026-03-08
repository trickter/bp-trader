from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


WEAK_ADMIN_TOKENS = {"", "dev-admin-token", "changeme", "admin"}
WEAK_DATABASE_MARKERS = ("postgres:postgres@",)


class Settings(BaseSettings):
    app_env: str = "development"
    allow_insecure_dev_defaults: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    database_url: str = "postgresql://postgres:postgres@localhost:5432/trader"
    admin_api_token: str = "dev-admin-token"
    backpack_mode: str = "mock"
    backpack_api_base_url: str = "https://api.backpack.exchange"
    backpack_api_key: str = ""
    backpack_private_key: str = ""
    backpack_window_ms: int = 5000
    backpack_default_symbol: str = "BTC_USDC_PERP"
    backpack_default_interval: str = "1h"
    backpack_default_price_source: str = "mark"
    backpack_default_market_type: str = "perp"
    backpack_account_label: str = "backpack-primary"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        allow_weak_defaults = self.allow_insecure_dev_defaults and self.app_env in {"development", "test"}

        if self.backpack_mode == "live" and (not self.backpack_api_key or not self.backpack_private_key):
            raise ValueError("BACKPACK_MODE=live requires BACKPACK_API_KEY and BACKPACK_PRIVATE_KEY.")

        if not allow_weak_defaults and self.admin_api_token in WEAK_ADMIN_TOKENS:
            raise ValueError(
                "ADMIN_API_TOKEN must be set to a non-default secret unless "
                "ALLOW_INSECURE_DEV_DEFAULTS=true in development or test."
            )

        if not allow_weak_defaults and any(marker in self.database_url for marker in WEAK_DATABASE_MARKERS):
            raise ValueError(
                "DATABASE_URL must not use default postgres credentials unless "
                "ALLOW_INSECURE_DEV_DEFAULTS=true in development or test."
            )

        return self


settings = Settings()
