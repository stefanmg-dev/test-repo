import os

import pytest
from fastapi.testclient import TestClient


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from api import app
from database import SessionLocal
from database_models import ProcessingRun
from processing_run_dependencies import (
    get_processing_run_review_service,
)
from processing_run_service import (
    ProcessingRunReviewService,
    ProcessingRunService,
)
from security_dependencies import get_optional_principal
from security_principal import SecurityPrincipal


TENANT_ID = "tenant-http-review"


def reviewer_principal():
    return SecurityPrincipal(
        principal_type="user",
        subject="http-reviewer-1",
        tenant_id=TENANT_ID,
        scopes=frozenset({"processing-runs:review"}),
    )


def test_review_http_persists_corrected_result_in_postgresql():
    session = SessionLocal()
    run_id = None

    previous_service_override = app.dependency_overrides.get(
        get_processing_run_review_service
    )
    previous_principal_override = app.dependency_overrides.get(
        get_optional_principal
    )

    app.dependency_overrides[
        get_processing_run_review_service
    ] = lambda: ProcessingRunReviewService(session)

    app.dependency_overrides[
        get_optional_principal
    ] = reviewer_principal

    try:
        processing_service = ProcessingRunService(session)

        run = processing_service.start_run(
            document_type="invoice",
            filename="http-review-integration.pdf",
            input_format="pdf",
            tenant_id=TENANT_ID,
            created_by_type="user",
            created_by_subject="creator-1",
        )
        run_id = run.id

        processing_service.complete_run(
            run.id,
            processing_status="review",
            profile="telecom_a1",
            requires_review=True,
            duration_ms=10,
            step_timings={"document_input_ms": 5},
            quality={
                "status": "review",
                "requires_review": True,
            },
            final_values={
                "invoice_number": "ORIGINAL",
            },
            collections={},
            validation={
                "fields": {
                    "valid": True,
                    "errors": {},
                },
            },
        )

        client = TestClient(app)
        review_url = (
            f"/api/v1/processing-runs/{run.id}/review"
        )

        pending_response = client.get(review_url)

        assert pending_response.status_code == 200
        assert pending_response.json()["status"] == "pending"
        assert pending_response.json()["effective_values"] == {
            "invoice_number": "ORIGINAL",
        }

        update_response = client.put(
            review_url,
            json={
                "status": "corrected",
                "corrected_values": {
                    "invoice_number": "CORRECTED",
                },
                "comment": "Confirmed through HTTP review",
            },
        )

        assert update_response.status_code == 200
        update_body = update_response.json()
        assert update_body["status"] == "corrected"
        assert update_body["original_values"] == {
            "invoice_number": "ORIGINAL",
        }
        assert update_body["corrected_values"] == {
            "invoice_number": "CORRECTED",
        }
        assert update_body["effective_values"] == {
            "invoice_number": "CORRECTED",
        }
        assert update_body["reviewed_by_subject"] == (
            "http-reviewer-1"
        )

        session.expire_all()
        persisted = session.get(ProcessingRun, run.id)

        assert persisted is not None
        assert persisted.tenant_id == TENANT_ID
        assert persisted.review_status == "corrected"
        assert persisted.final_values == {
            "invoice_number": "ORIGINAL",
        }
        assert persisted.corrected_values == {
            "invoice_number": "CORRECTED",
        }
        assert persisted.reviewed_by_type == "user"
        assert persisted.reviewed_by_subject == (
            "http-reviewer-1"
        )

        retrieved_response = client.get(review_url)

        assert retrieved_response.status_code == 200
        assert retrieved_response.json()["effective_values"] == {
            "invoice_number": "CORRECTED",
        }

        conflict_response = client.put(
            review_url,
            json={"status": "approved"},
        )

        assert conflict_response.status_code == 409
        assert conflict_response.json()["detail"] == (
            "Processing run review is already completed"
        )

    finally:
        session.rollback()

        if run_id is not None:
            persisted = session.get(ProcessingRun, run_id)
            if persisted is not None:
                session.delete(persisted)
                session.commit()

        session.close()

        if previous_service_override is None:
            app.dependency_overrides.pop(
                get_processing_run_review_service,
                None,
            )
        else:
            app.dependency_overrides[
                get_processing_run_review_service
            ] = previous_service_override

        if previous_principal_override is None:
            app.dependency_overrides.pop(
                get_optional_principal,
                None,
            )
        else:
            app.dependency_overrides[
                get_optional_principal
            ] = previous_principal_override
