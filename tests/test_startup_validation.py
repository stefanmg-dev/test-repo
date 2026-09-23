from pathlib import Path
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine

import startup_validation
from startup_validation import (
    StartupValidationError,
    validate_database_startup,
)


def test_startup_validation_accepts_connected_current_database(
    monkeypatch,
):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(
        startup_validation,
        "get_expected_revisions",
        lambda config_path: (),
    )

    result = validate_database_startup(
        engine,
        config_path=Path("unused.ini"),
    )

    assert result.database_connected is True
    assert result.current_revisions == ()
    assert result.expected_revisions == ()


def test_startup_validation_rejects_revision_mismatch(
    monkeypatch,
):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(
        startup_validation,
        "get_expected_revisions",
        lambda config_path: ("expected",),
    )

    with pytest.raises(
        StartupValidationError,
        match="Database migration revision mismatch",
    ):
        validate_database_startup(
            engine,
            config_path=Path("unused.ini"),
        )


def test_startup_validation_wraps_connectivity_failure():
    engine = Mock()
    engine.connect.side_effect = OSError(
        "database unavailable"
    )

    with pytest.raises(
        StartupValidationError,
        match="Database startup validation failed",
    ) as exc_info:
        validate_database_startup(engine)

    assert isinstance(exc_info.value.__cause__, OSError)


def test_repository_database_matches_alembic_head():
    from database import engine

    result = validate_database_startup(engine)

    assert result.database_connected is True
    assert result.current_revisions
    assert result.current_revisions == (
        result.expected_revisions
    )
