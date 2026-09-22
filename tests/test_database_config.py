import pytest

import database_config


def test_get_database_url_from_environment(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user@/database",
    )

    assert database_config.get_database_url() == (
        "postgresql+psycopg://user@/database"
    )


def test_get_database_url_is_required(monkeypatch):
    monkeypatch.setattr(
        database_config,
        "load_environment",
        lambda: None,
    )
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(
        RuntimeError,
        match="DATABASE_URL environment variable is required",
    ):
        database_config.get_database_url()
