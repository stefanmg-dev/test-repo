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
    max_upload_size_bytes: int = Field(
        default=20 * 1024 * 1024,
        ge=1024,
        le=200 * 1024 * 1024,
        validation_alias="MAX_UPLOAD_SIZE_BYTES",
    )
    max_filename_length: int = Field(
        default=255,
        ge=1,
        le=1024,
        validation_alias="MAX_FILENAME_LENGTH",
    )
    max_pdf_pages: int = Field(
        default=50,
        ge=1,
        le=1000,
        validation_alias="MAX_PDF_PAGES",
    )
    max_image_width: int = Field(
        default=20000,
        ge=1,
        le=100000,
        validation_alias="MAX_IMAGE_WIDTH",
    )
    max_image_height: int = Field(
        default=20000,
        ge=1,
        le=100000,
        validation_alias="MAX_IMAGE_HEIGHT",
    )
    max_image_pixels: int = Field(
        default=100_000_000,
        ge=1,
        le=1_000_000_000,
        validation_alias="MAX_IMAGE_PIXELS",
    )
    allowed_hosts: str = Field(
        default="localhost,127.0.0.1,testserver",
        validation_alias="ALLOWED_HOSTS",
    )
    cors_allowed_origins: str = Field(
        default="",
        validation_alias="CORS_ALLOWED_ORIGINS",
    )
    expose_api_docs: bool = Field(
        default=True,
        validation_alias="EXPOSE_API_DOCS",
    )

    def allowed_hosts_list(self) -> list[str]:
        hosts = [
            value.strip()
            for value in self.allowed_hosts.split(",")
            if value.strip()
        ]
        if not hosts:
            raise ValueError("ALLOWED_HOSTS must not be empty")
        return hosts

    def cors_allowed_origins_list(self) -> list[str]:
        return [
            value.strip()
            for value in self.cors_allowed_origins.split(",")
            if value.strip()
        ]

    def api_docs_enabled(self) -> bool:
        return self.expose_api_docs

    def database_url_value(self) -> str:
        return self.database_url.get_secret_value()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
