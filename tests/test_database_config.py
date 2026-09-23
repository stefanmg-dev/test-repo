import pytest

import database_config
from app_settings import clear_settings_cache


def test_get_database_url_from_environment(monkeypatch):
    clear_settings_cache()
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user@/database",
    )

    assert database_config.get_database_url() == (
        "postgresql+psycopg://user@/database"
    )


def test_get_database_url_is_required(monkeypatch):
    clear_settings_cache()
    monkeypatch.delenv("DATABASE_URL", raising=False)

    monkeypatch.setattr(
        database_config,
        "get_settings",
        lambda: database_config.AppSettings(
            _env_file=None
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="DATABASE_URL environment variable is required",
    ):
        database_config.get_database_url()


def teardown_module():
    clear_settings_cache()
