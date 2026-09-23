from types import SimpleNamespace

from fastapi.testclient import TestClient

import api
from api import app
from startup_validation import StartupValidationError


def test_health_is_liveness_only(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "Liveness must not check database readiness"
        )

    monkeypatch.setattr(
        api,
        "validate_database_startup",
        fail_if_called,
    )

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_ready_reports_database_and_migration_state(
    monkeypatch,
):
    monkeypatch.setattr(
        api,
        "validate_database_startup",
        lambda engine: SimpleNamespace(
            current_revisions=("revision-123",),
        ),
    )

    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "connected",
        "migrations": "current",
        "revision": "revision-123",
    }
    assert response.headers["X-Request-ID"]


def test_ready_returns_503_when_validation_fails(
    monkeypatch,
):
    def fail_validation(engine):
        raise StartupValidationError(
            "Database startup validation failed"
        )

    monkeypatch.setattr(
        api,
        "validate_database_startup",
        fail_validation,
    )

    response = TestClient(app).get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
    }
    assert response.headers["X-Request-ID"]
