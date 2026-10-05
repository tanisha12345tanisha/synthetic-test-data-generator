from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


EnvironmentName = Literal[
    "development",
    "test",
    "staging",
    "production",
]


class Settings(BaseSettings):
    app_name: str = "Synthetic Test Data Generator"
    app_version: str = "2.0.0"
    app_environment: EnvironmentName = "development"
    app_debug: bool = False

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres"
        "@localhost:5432/synthetic_data_generator"
    )
    test_database_url: str | None = None
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=100)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)
    database_pool_recycle_seconds: int = Field(default=1800, ge=60)

    access_token_secret: str = (
        "development-access-token-secret-change-me"
    )
    refresh_token_secret: str = (
        "development-refresh-token-secret-change-me"
    )
    access_token_expiry_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expiry_days: int = Field(default=7, ge=1, le=365)
    password_reset_token_expiry_minutes: int = Field(default=30, ge=5, le=1440)

    frontend_url: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_starttls: bool = True

    generated_file_retention_hours: int = Field(default=24, ge=1)
    maximum_tables_per_dataset: int = Field(default=5, ge=1, le=20)
    maximum_rows_per_table: int = Field(default=10000, ge=1)
    maximum_total_rows_per_dataset: int = Field(default=50000, ge=1)

    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]
        return value

    @field_validator("database_url", "test_database_url")
    @classmethod
    def validate_database_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized_value = value.strip()
        supported_prefixes = (
            "postgresql+asyncpg://",
            "sqlite+aiosqlite://",
        )

        if not normalized_value.startswith(supported_prefixes):
            raise ValueError(
                "Database URLs must use 'postgresql+asyncpg://' "
                "or 'sqlite+aiosqlite://'."
            )

        return normalized_value

    @field_validator("refresh_token_secret")
    @classmethod
    def ensure_distinct_token_secrets(cls, value: str, info) -> str:
        access_token_secret = info.data.get("access_token_secret")

        if access_token_secret and value == access_token_secret:
            raise ValueError(
                "ACCESS_TOKEN_SECRET and REFRESH_TOKEN_SECRET must be different."
            )

        return value

    @field_validator("maximum_total_rows_per_dataset")
    @classmethod
    def validate_total_row_limit(cls, value: int, info) -> int:
        maximum_rows_per_table = info.data.get("maximum_rows_per_table")

        if maximum_rows_per_table is not None and value < maximum_rows_per_table:
            raise ValueError(
                "MAXIMUM_TOTAL_ROWS_PER_DATASET cannot be lower than "
                "MAXIMUM_ROWS_PER_TABLE."
            )

        return value

    @property
    def is_development(self) -> bool:
        return self.app_environment == "development"

    @property
    def is_test(self) -> bool:
        return self.app_environment == "test"

    @property
    def is_production(self) -> bool:
        return self.app_environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
