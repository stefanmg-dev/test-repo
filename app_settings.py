from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    environment: Literal[
        "development",
        "test",
        "production",
    ] = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )
    log_level: Literal[
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ] = Field(
        default="INFO",
        validation_alias="LOG_LEVEL",
    )
    database_url: SecretStr = Field(
        validation_alias="DATABASE_URL",
        repr=False,
    )
    database_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        validation_alias="DATABASE_POOL_SIZE",
    )
    database_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        validation_alias="DATABASE_MAX_OVERFLOW",
    )
    database_pool_timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        validation_alias="DATABASE_POOL_TIMEOUT_SECONDS",
    )

    def database_url_value(self) -> str:
        return self.database_url.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
