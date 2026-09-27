from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api import app
from processing_run_dependencies import (
    get_processing_run_review_service,
)
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunReviewError,
)
from security_dependencies import get_optional_principal
from security_principal import SecurityPrincipal


NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)


def principal(*scopes):
    return SecurityPrincipal(
        principal_type="user",
        subject="reviewer-1",
        tenant_id="tenant-1",
        scopes=frozenset(scopes),
    )


def review_run(status="pending"):
    return SimpleNamespace(
        id=uuid4(),
        requires_review=True,
        review_status=status,
        final_values={"invoice_number": "ORIGINAL"},
        corrected_values=None,
        review_comment=None,
        reviewed_at=None,
        reviewed_by_type=None,
        reviewed_by_subject=None,
    )


class ReviewService:
    def __init__(self, run=None):
        self.run = run or review_run()
        self.get_calls = []
        self.review_calls = []
        self.get_error = None
        self.review_error = None

    def get_review_run(self, run_id, *, tenant_id=None):
        self.get_calls.append((run_id, tenant_id))
        if self.get_error:
            raise self.get_error
        return self.run

    def review_run(self, run_id, **kwargs):
        self.review_calls.append((run_id, kwargs))
        if self.review_error:
            raise self.review_error

        self.run.review_status = kwargs["status"]
        self.run.corrected_values = kwargs["corrected_values"]
        self.run.review_comment = kwargs["comment"]
        self.run.reviewed_at = NOW
        self.run.reviewed_by_type = kwargs["reviewed_by_type"]
        self.run.reviewed_by_subject = kwargs[
            "reviewed_by_subject"
        ]
        return self.run


@pytest.fixture
def install_review_service():
    service = ReviewService()
    app.dependency_overrides[
        get_processing_run_review_service
    ] = lambda: service
    app.dependency_overrides[
        get_optional_principal
    ] = lambda: principal("processing-runs:review")

    yield service

    app.dependency_overrides.pop(
        get_processing_run_review_service,
        None,
    )
    app.dependency_overrides.pop(
        get_optional_principal,
        None,
    )


def test_get_pending_review(install_review_service):
    service = install_review_service

    response = TestClient(app).get(
        f"/api/v1/processing-runs/{service.run.id}/review"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["original_values"] == {
        "invoice_number": "ORIGINAL"
    }
    assert response.json()["effective_values"] == {
        "invoice_number": "ORIGINAL"
    }
    assert service.get_calls == [
        (service.run.id, "tenant-1")
    ]


def test_corrects_review_and_preserves_original_values(
    install_review_service,
):
    service = install_review_service

    response = TestClient(app).put(
        f"/api/v1/processing-runs/{service.run.id}/review",
        json={
            "status": "corrected",
            "corrected_values": {
                "invoice_number": "CORRECTED",
            },
            "comment": "Confirmed from document",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "corrected"
    assert body["original_values"] == {
        "invoice_number": "ORIGINAL"
    }
    assert body["corrected_values"] == {
        "invoice_number": "CORRECTED"
    }
    assert body["effective_values"] == {
        "invoice_number": "CORRECTED"
    }

    call = service.review_calls[0][1]
    assert call["tenant_id"] == "tenant-1"
    assert call["reviewed_by_type"] == "user"
    assert call["reviewed_by_subject"] == "reviewer-1"


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_accepts_terminal_review_statuses(
    install_review_service,
    status,
):
    service = install_review_service

    response = TestClient(app).put(
        f"/api/v1/processing-runs/{service.run.id}/review",
        json={"status": status},
    )

    assert response.status_code == 200
    assert response.json()["status"] == status


def test_review_returns_404_for_inaccessible_run(
    install_review_service,
):
    service = install_review_service
    service.get_error = ProcessingRunNotFoundError(
        f"Processing run '{service.run.id}' was not found"
    )

    response = TestClient(app).get(
        f"/api/v1/processing-runs/{service.run.id}/review"
    )

    assert response.status_code == 404


def test_completed_review_returns_409(
    install_review_service,
):
    service = install_review_service
    service.review_error = ProcessingRunReviewError(
        "Processing run review is already completed"
    )

    response = TestClient(app).put(
        f"/api/v1/processing-runs/{service.run.id}/review",
        json={"status": "approved"},
    )

    assert response.status_code == 409


def test_review_requires_review_scope(
    install_review_service,
):
    service = install_review_service
    app.dependency_overrides[
        get_optional_principal
    ] = lambda: principal("processing-runs:read")

    response = TestClient(app).get(
        f"/api/v1/processing-runs/{service.run.id}/review"
    )

    assert response.status_code == 403


def test_review_rejects_invalid_payload(
    install_review_service,
):
    service = install_review_service

    response = TestClient(app).put(
        f"/api/v1/processing-runs/{service.run.id}/review",
        json={"status": "unknown"},
    )

    assert response.status_code == 422
