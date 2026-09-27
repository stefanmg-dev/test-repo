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
        review_status=None,
        reviewed_at=None,
        corrected_values=None,
        configuration_hash=None,
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

    def review_summary(self, tenant_id=None):
        self.review_summary_tenant_id = tenant_id
        return {
            "total_requiring_review": 10,
            "pending": 4,
            "approved": 2,
            "corrected": 3,
            "rejected": 1,
            "average_review_duration_ms": 1500,
        }

    def get_run(self, run_id, *, tenant_id=None):
        if run_id != self.run.id:
            raise ProcessingRunNotFoundError(
                f"Processing run '{run_id}' was not found"
            )
        return self.run

    def list_runs(
        self,
        *,
        offset,
        limit,
        document_type=None,
        processing_status=None,
        profile=None,
        requires_review=None, review_status=None,
        tenant_id=None,
    ):
        self.list_calls.append(
            {
                "offset": offset,
                "limit": limit,
                "document_type": document_type,
                "processing_status": processing_status,
                "profile": profile,
                "requires_review": requires_review,
                "tenant_id": tenant_id,
            }
        )
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
        "/api/v1/processing-runs"
        "?offset=5"
        "&limit=10"
        "&document_type=invoice"
        "&processing_status=accepted"
        "&profile=telecom_a1"
        "&requires_review=false"
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["offset"] == 5
    assert response.json()["limit"] == 10
    assert response.json()["items"][0]["id"] == (
        str(service.run.id)
    )
    assert "final_values" not in response.json()["items"][0]
    assert service.list_calls == [
        {
            "offset": 5,
            "limit": 10,
            "document_type": "invoice",
            "processing_status": "accepted",
            "profile": "telecom_a1",
            "requires_review": False,
            "tenant_id": "default",
        }
    ]


def test_list_processing_runs_validates_limit():
    response = TestClient(app).get(
        "/api/v1/processing-runs?limit=101"
    )

    assert response.status_code == 422


def test_list_processing_runs_validates_status():
    response = TestClient(app).get(
        "/api/v1/processing-runs"
        "?processing_status=unknown"
    )

    assert response.status_code == 422


def test_list_processing_runs_validates_profile():
    response = TestClient(app).get(
        "/api/v1/processing-runs?profile=INVALID-PROFILE"
    )

    assert response.status_code == 422



def test_get_processing_run_review_summary():
    service = QueryService()
    install(service)

    response = TestClient(app).get(
        "/api/v1/processing-runs/review-summary"
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_requiring_review": 10,
        "pending": 4,
        "approved": 2,
        "corrected": 3,
        "rejected": 1,
        "average_review_duration_ms": 1500,
    }
    assert service.review_summary_tenant_id == "default"


def test_get_extraction_quality_analysis():
    service = QueryService()
    service.extraction_quality_analysis = lambda tenant_id=None: {
        "corrected_runs": 1,
        "groups": [
            {
                "document_type": "invoice",
                "profile": "telecom_a1",
                "configuration_hash": "hash-a",
                "corrected_runs": 1,
                "field_counts": {
                    "total": 2,
                    "unchanged": 1,
                    "changed": 1,
                    "added": 0,
                    "removed": 0,
                },
                "corrections": 1,
                "correction_rate": 0.5,
                "field_corrections": [
                    {
                        "field_name": "invoice_number",
                        "corrections": 1,
                    }
                ],
            }
        ],
    }
    install(service)

    response = TestClient(app).get(
        "/api/v1/processing-runs/extraction-quality"
    )

    assert response.status_code == 200
    assert response.json()["corrected_runs"] == 1
    assert response.json()["groups"][0][
        "configuration_hash"
    ] == "hash-a"
    assert response.json()["groups"][0][
        "field_corrections"
    ] == [
        {
            "field_name": "invoice_number",
            "corrections": 1,
        }
    ]


def test_export_processing_runs_as_csv():
    service = QueryService()
    service.export_tenant_id = None

    def export_runs(tenant_id=None):
        service.export_tenant_id = tenant_id
        return [service.run]

    service.export_runs = export_runs
    install(service)

    response = TestClient(app).get(
        "/api/v1/processing-runs/export"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/csv"
    )
    assert response.headers["content-disposition"] == (
        'attachment; filename="processing-runs.csv"'
    )
    assert service.export_tenant_id == "default"
    assert "processing_run_id,document_type" in response.text
    assert str(service.run.id) in response.text
    assert "raw_text" not in response.text
