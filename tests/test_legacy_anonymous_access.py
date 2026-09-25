from types import SimpleNamespace

from fastapi.testclient import TestClient

from api import app
import security_scopes
from processing_run_dependencies import get_processing_run_service
from security_dependencies import get_optional_principal


class QueryService:
    def list_runs(self, **kwargs):
        return [], 0


def install_anonymous(monkeypatch, enabled):
    app.dependency_overrides[get_optional_principal] = lambda: None
    app.dependency_overrides[get_processing_run_service] = (
        lambda: QueryService()
    )
    monkeypatch.setattr(
        security_scopes,
        "get_settings",
        lambda: SimpleNamespace(
            legacy_anonymous_access_enabled=enabled
        ),
    )


def test_history_requires_authentication_when_legacy_access_is_disabled(
    monkeypatch,
):
    install_anonymous(monkeypatch, False)

    response = TestClient(app).get("/api/v1/processing-runs")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert response.headers["WWW-Authenticate"] == "APIKey, Bearer"


def test_history_remains_compatible_when_legacy_access_is_enabled(
    monkeypatch,
):
    install_anonymous(monkeypatch, True)

    response = TestClient(app).get("/api/v1/processing-runs")

    assert response.status_code == 200


def test_health_remains_public_when_legacy_access_is_disabled(
    monkeypatch,
):
    install_anonymous(monkeypatch, False)

    response = TestClient(app).get("/health")

    assert response.status_code == 200
