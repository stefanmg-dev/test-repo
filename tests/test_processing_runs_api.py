from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from api import app
from processing_run_dependencies import (
    get_processing_run_service,
)
from processing_run_service import ProcessingRunNotFoundError


NOW = datetime(2026, 9, 22, tzinfo=timezone.utc)


def build_run():
    return SimpleNamespace(
        id=uuid4(),
        document_type="invoice",
        profile="telecom_a1",
        filename="invoice.pdf",
        input_format="pdf",
        processing_status="accepted",
        requires_review=False,
        started_at=NOW,
        completed_at=NOW,
        duration_ms=123,
        step_timings={"document_input_ms": 10},
        quality={"status": "accepted"},
        final_values={"invoice_number": "123"},
        collections={},
        validation={"fields": {"valid": True}},
        error=None,
        created_at=NOW,
        updated_at=NOW,
    )


class QueryService:
    def __init__(self, run=None):
        self.run = run or build_run()
        self.list_calls = []

    def get_run(self, run_id):
        if run_id != self.run.id:
            raise ProcessingRunNotFoundError(
                f"Processing run '{run_id}' was not found"
            )
        return self.run

    def list_runs(self, *, offset, limit):
        self.list_calls.append((offset, limit))
        return [self.run], 1


def install(service):
    app.dependency_overrides[
        get_processing_run_service
    ] = lambda: service


def test_get_processing_run():
    service = QueryService()
    install(service)

    response = TestClient(app).get(
        f"/api/v1/processing-runs/{service.run.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(service.run.id)
    assert response.json()["step_timings"] == {
        "document_input_ms": 10
    }


def test_get_processing_run_returns_404():
    service = QueryService()
    install(service)
    missing_id = uuid4()

    response = TestClient(app).get(
        f"/api/v1/processing-runs/{missing_id}"
    )

    assert response.status_code == 404
    assert str(missing_id) in response.json()["detail"]


def test_list_processing_runs_uses_pagination():
    service = QueryService()
    install(service)

    response = TestClient(app).get(
        "/api/v1/processing-runs?offset=5&limit=10"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["offset"] == 5
    assert response.json()["limit"] == 10
    assert response.json()["items"][0]["id"] == (
        str(service.run.id)
    )
    assert "final_values" not in response.json()["items"][0]
    assert service.list_calls == [(5, 10)]


def test_list_processing_runs_validates_limit():
    response = TestClient(app).get(
        "/api/v1/processing-runs?limit=101"
    )

    assert response.status_code == 422
