from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import routes_extract
from api import app
from processing_run_dependencies import get_processing_run_service
from security_dependencies import get_optional_principal
from security_principal import SecurityPrincipal


NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)


class Service:
    def __init__(self):
        self.run_id = uuid4()
        self.started = []

    def start_run(self, **kwargs):
        self.started.append(kwargs)
        return SimpleNamespace(id=self.run_id)

    def complete_run(self, run_id, **kwargs):
        return None

    def fail_run(self, run_id, **kwargs):
        return None

    def get_run(self, run_id, *, tenant_id=None):
        return SimpleNamespace(
            id=run_id,
            document_type="invoice",
            profile=None,
            filename="scope.pdf",
            input_format="pdf",
            processing_status="accepted",
            requires_review=False,
            started_at=NOW,
            completed_at=NOW,
            duration_ms=1,
            step_timings={},
            quality={},
            final_values={},
            collections={},
            validation={},
            error=None,
            created_at=NOW,
            updated_at=NOW,
        )

    def list_runs(self, **kwargs):
        return [], 0


def auth_principal(*scopes):
    return SecurityPrincipal(
        principal_type="service",
        subject="service-1",
        tenant_id="tenant-1",
        scopes=frozenset(scopes),
    )


def install(service, configured_principal):
    app.dependency_overrides[get_processing_run_service] = lambda: service
    app.dependency_overrides[get_optional_principal] = (
        lambda: configured_principal
    )


def test_history_rejects_authenticated_principal_without_read_scope():
    service = Service()
    install(service, auth_principal("documents:extract"))

    response = TestClient(app).get("/api/v1/processing-runs")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Missing required scope: processing-runs:read"
    }


def test_history_accepts_processing_runs_read_scope():
    service = Service()
    install(service, auth_principal("processing-runs:read"))

    response = TestClient(app).get("/api/v1/processing-runs")

    assert response.status_code == 200


def test_extract_rejects_authenticated_principal_without_extract_scope(
    monkeypatch,
):
    service = Service()
    install(service, auth_principal("processing-runs:read"))
    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: {"invoice": {"fields": []}},
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={"file": ("scope.pdf", b"test", "application/pdf")},
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Missing required scope: documents:extract"
    }
    assert service.started == []


def test_legacy_requests_remain_compatible():
    service = Service()
    install(service, None)

    response = TestClient(app).get("/api/v1/processing-runs")

    assert response.status_code == 200
