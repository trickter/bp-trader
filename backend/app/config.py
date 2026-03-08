from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
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


settings = Settings()
