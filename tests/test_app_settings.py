import pytest
from pydantic import ValidationError

from app_settings import AppSettings


def test_settings_read_and_validate_environment(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("DATABASE_POOL_SIZE", "12")
    monkeypatch.setenv("DATABASE_MAX_OVERFLOW", "24")
    monkeypatch.setenv(
        "DATABASE_POOL_TIMEOUT_SECONDS",
        "45",
    )

    settings = AppSettings(_env_file=None)

    assert settings.environment == "production"
    assert settings.log_level == "WARNING"
    assert settings.database_pool_size == 12
    assert settings.database_max_overflow == 24
    assert settings.database_pool_timeout_seconds == 45
    assert settings.database_url_value().endswith(
        "user:secret@localhost/db"
    )


def test_settings_require_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_settings_hide_database_credentials(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )

    settings = AppSettings(_env_file=None)
    representation = repr(settings)
    dumped = str(settings)

    assert "secret" not in representation
    assert "secret" not in dumped
    assert "database_url" not in representation
    assert "database_url" not in dumped


def test_settings_reject_invalid_pool_configuration(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )
    monkeypatch.setenv("DATABASE_POOL_SIZE", "0")

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_oidc_settings_require_complete_configuration(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )
    monkeypatch.setenv("OIDC_ENABLED", "true")
    monkeypatch.delenv("OIDC_ISSUER", raising=False)
    monkeypatch.delenv("OIDC_AUDIENCE", raising=False)
    monkeypatch.delenv("OIDC_JWKS_URL", raising=False)

    with pytest.raises(ValidationError):
        AppSettings(_env_file=None)


def test_oidc_settings_parse_algorithms(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )
    monkeypatch.setenv("OIDC_ENABLED", "true")
    monkeypatch.setenv("OIDC_ISSUER", "https://issuer.example")
    monkeypatch.setenv("OIDC_AUDIENCE", "api-audience")
    monkeypatch.setenv("OIDC_JWKS_URL", "https://issuer.example/keys")
    monkeypatch.setenv("OIDC_ALGORITHMS", "RS256, RS384")

    settings = AppSettings(_env_file=None)

    assert settings.oidc_algorithms_list() == ["RS256", "RS384"]


def test_legacy_anonymous_access_is_enabled_by_default(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )

    settings = AppSettings(_env_file=None)

    assert settings.legacy_anonymous_access_enabled is True


def test_legacy_anonymous_access_can_be_disabled(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:secret@localhost/db",
    )
    monkeypatch.setenv(
        "LEGACY_ANONYMOUS_ACCESS_ENABLED",
        "false",
    )

    settings = AppSettings(_env_file=None)

    assert settings.legacy_anonymous_access_enabled is False
