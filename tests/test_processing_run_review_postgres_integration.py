import os

import pytest


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from database import SessionLocal
from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunReviewError,
    ProcessingRunReviewService,
    ProcessingRunService,
)


def test_processing_run_review_lifecycle_in_postgresql():
    session = SessionLocal()
    run_id = None

    try:
        processing_service = ProcessingRunService(session)
        review_service = ProcessingRunReviewService(session)

        run = processing_service.start_run(
            document_type="invoice",
            filename="review-integration.pdf",
            input_format="pdf",
            tenant_id="tenant-review",
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

        pending = review_service.get_review_run(
            run.id,
            tenant_id="tenant-review",
        )

        assert pending.review_status == "pending"
        assert pending.corrected_values is None

        with pytest.raises(ProcessingRunNotFoundError):
            review_service.get_review_run(
                run.id,
                tenant_id="other-tenant",
            )

        reviewed = review_service.review_run(
            run.id,
            status="corrected",
            reviewed_by_type="user",
            reviewed_by_subject="reviewer-1",
            tenant_id="tenant-review",
            corrected_values={
                "invoice_number": "CORRECTED",
            },
            comment="Confirmed from document",
        )

        session.expire_all()
        persisted = session.get(ProcessingRun, run.id)

        assert persisted is not None
        assert reviewed.review_status == "corrected"
        assert persisted.review_status == "corrected"
        assert persisted.final_values == {
            "invoice_number": "ORIGINAL",
        }
        assert persisted.corrected_values == {
            "invoice_number": "CORRECTED",
        }
        assert persisted.reviewed_by_type == "user"
        assert persisted.reviewed_by_subject == "reviewer-1"
        assert persisted.review_comment == (
            "Confirmed from document"
        )
        assert persisted.reviewed_at is not None
        assert review_service.effective_values(
            persisted
        ) == {
            "invoice_number": "CORRECTED",
        }

        with pytest.raises(
            ProcessingRunReviewError,
            match="already completed",
        ):
            review_service.review_run(
                run.id,
                status="approved",
                reviewed_by_type="user",
                reviewed_by_subject="reviewer-2",
                tenant_id="tenant-review",
            )

    finally:
        session.rollback()

        if run_id is not None:
            persisted = session.get(ProcessingRun, run_id)
            if persisted is not None:
                session.delete(persisted)
                session.commit()

        session.close()
