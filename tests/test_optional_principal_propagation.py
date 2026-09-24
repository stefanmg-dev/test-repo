from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import routes_extract
from api import app
from processing_run_dependencies import get_processing_run_service
from security_dependencies import get_optional_api_key_principal
from security_principal import SecurityPrincipal


NOW = datetime(2026, 9, 24, tzinfo=timezone.utc)
PRINCIPAL = SecurityPrincipal(
    principal_type="service",
    subject="service-tenant-a",
    tenant_id="tenant-a",
    scopes=frozenset({"documents:extract", "processing-runs:read"}),
)


class RecordingService:
    def __init__(self):
        self.run_id = uuid4()
        self.started = []
        self.get_calls = []
        self.list_calls = []

    def start_run(self, **kwargs):
        self.started.append(kwargs)
        return SimpleNamespace(id=self.run_id)

    def complete_run(self, run_id, **kwargs):
        return None

    def fail_run(self, run_id, **kwargs):
        return None

    def get_run(self, run_id, *, tenant_id=None):
        self.get_calls.append((run_id, tenant_id))
        return SimpleNamespace(
            id=run_id,
            document_type="invoice",
            profile=None,
            filename="tenant.pdf",
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
        self.list_calls.append(kwargs)
        return [], 0


def install(service):
    app.dependency_overrides[get_processing_run_service] = lambda: service
    app.dependency_overrides[get_optional_api_key_principal] = lambda: PRINCIPAL


def test_extraction_persists_authenticated_principal(monkeypatch):
    service = RecordingService()
    install(service)
    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: {
            "invoice": {
                "fields": [
                    {
                        "name": "invoice_number",
                        "type": "constant",
                        "value": "1",
                        "validation": [],
                    }
                ]
            }
        },
    )

    async def input_result(file):
        return {
            "text": "test text",
            "quality": {
                "status": "accepted",
                "requires_review": False,
                "input": {
                    "format": "PDF",
                    "source": "native_pdf",
                    "page_count": 1,
                },
                "warnings": [],
            },
        }

    monkeypatch.setattr(routes_extract, "extract_document_input", input_result)
    monkeypatch.setattr(routes_extract, "extract_values", lambda text: {})
    monkeypatch.setattr(
        routes_extract,
        "extract_document_data",
        lambda **kwargs: {
            "fields": {"invoice_number": "1"},
            "collections": {},
        },
    )
    monkeypatch.setattr(
        routes_extract,
        "validate_result",
        lambda **kwargs: {"valid": True, "errors": {}},
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={"file": ("tenant.pdf", b"test", "application/pdf")},
    )

    assert response.status_code == 200
    assert service.started[0]["tenant_id"] == "tenant-a"
    assert service.started[0]["created_by_type"] == "service"
    assert service.started[0]["created_by_subject"] == "service-tenant-a"


def test_history_routes_propagate_principal_tenant():
    service = RecordingService()
    install(service)
    client = TestClient(app)

    detail = client.get(f"/api/v1/processing-runs/{service.run_id}")
    listing = client.get("/api/v1/processing-runs")

    assert detail.status_code == 200
    assert listing.status_code == 200
    assert service.get_calls == [(service.run_id, "tenant-a")]
    assert service.list_calls[0]["tenant_id"] == "tenant-a"
