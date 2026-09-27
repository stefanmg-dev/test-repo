import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from database import SessionLocal
from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunReviewService,
    ProcessingRunService,
)


def test_review_summary_aggregates_tenant_metrics():
    session = SessionLocal()
    tenant_id = f"review-summary-{uuid4()}"
    created_ids = []
    completed_at = datetime(
        2026,
        9,
        20,
        10,
        0,
        tzinfo=timezone.utc,
    )

    try:
        processing_service = ProcessingRunService(session)
        review_service = ProcessingRunReviewService(session)

        runs = []

        for index in range(4):
            run = processing_service.start_run(
                document_type="invoice",
                filename=f"summary-{index}.pdf",
                input_format="pdf",
                tenant_id=tenant_id,
            )
            created_ids.append(run.id)

            completed = processing_service.complete_run(
                run.id,
                processing_status="review",
                profile="telecom_a1",
                requires_review=True,
                duration_ms=100,
                step_timings={},
                quality={
                    "status": "review",
                    "requires_review": True,
                },
                final_values={"index": index},
                collections={},
                validation={},
                completed_at=completed_at,
            )
            runs.append(completed)

        decisions = [
            ("approved", None, 1000),
            (
                "corrected",
                {"index": "corrected"},
                2000,
            ),
            ("rejected", None, 3000),
        ]

        for run, decision in zip(runs[:3], decisions):
            status, corrected_values, duration_ms = decision

            review_service.review_run(
                run.id,
                status=status,
                reviewed_by_type="user",
                reviewed_by_subject="reviewer-1",
                tenant_id=tenant_id,
                corrected_values=corrected_values,
                reviewed_at=(
                    completed_at
                    + timedelta(milliseconds=duration_ms)
                ),
            )

        summary = processing_service.review_summary(
            tenant_id=tenant_id,
        )

        assert summary == {
            "total_requiring_review": 4,
            "pending": 1,
            "approved": 1,
            "corrected": 1,
            "rejected": 1,
            "average_review_duration_ms": 2000,
        }

        other_tenant_summary = (
            processing_service.review_summary(
                tenant_id=f"other-{uuid4()}",
            )
        )

        assert other_tenant_summary == {
            "total_requiring_review": 0,
            "pending": 0,
            "approved": 0,
            "corrected": 0,
            "rejected": 0,
            "average_review_duration_ms": None,
        }

    finally:
        session.rollback()

        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()

        session.close()
