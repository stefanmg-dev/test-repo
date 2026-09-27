import os
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


def test_quality_analysis_groups_corrected_reviews_by_identity():
    session = SessionLocal()
    tenant_id = f"quality-{uuid4()}"
    created_ids = []

    try:
        processing_service = ProcessingRunService(session)
        review_service = ProcessingRunReviewService(session)

        cases = [
            (
                "telecom_a1",
                "hash-a",
                {"invoice_number": "100"},
                {"invoice_number": "101"},
            ),
            (
                "telecom_a1",
                "hash-a",
                {
                    "invoice_number": "200",
                    "supplier_name": "A1",
                },
                {
                    "invoice_number": "201",
                    "supplier_name": "A1",
                },
            ),
            (
                "electricity_electrohold",
                "hash-b",
                {"total_amount": "30.00"},
                {"total_amount": "31.00"},
            ),
        ]

        for index, case in enumerate(cases):
            profile, config_hash, original, corrected = case

            run = processing_service.start_run(
                document_type="invoice",
                filename=f"quality-{index}.pdf",
                input_format="pdf",
                tenant_id=tenant_id,
            )
            created_ids.append(run.id)

            processing_service.complete_run(
                run.id,
                processing_status="review",
                profile=profile,
                requires_review=True,
                duration_ms=10,
                step_timings={},
                quality={
                    "status": "review",
                    "requires_review": True,
                },
                final_values=original,
                collections={},
                validation={},
                configuration_hash=config_hash,
            )

            review_service.review_run(
                run.id,
                status="corrected",
                reviewed_by_type="user",
                reviewed_by_subject="reviewer-1",
                tenant_id=tenant_id,
                corrected_values=corrected,
            )

        result = processing_service.extraction_quality_analysis(
            tenant_id=tenant_id,
        )

        assert result["corrected_runs"] == 3
        assert len(result["groups"]) == 2

        a1 = next(
            group
            for group in result["groups"]
            if group["profile"] == "telecom_a1"
        )

        assert a1["configuration_hash"] == "hash-a"
        assert a1["corrected_runs"] == 2
        assert a1["field_counts"] == {
            "total": 3,
            "unchanged": 1,
            "changed": 2,
            "added": 0,
            "removed": 0,
        }
        assert a1["corrections"] == 2
        assert a1["field_corrections"] == [
            {
                "field_name": "invoice_number",
                "corrections": 2,
            }
        ]

        isolated = (
            processing_service.extraction_quality_analysis(
                tenant_id=f"other-{uuid4()}",
            )
        )

        assert isolated == {
            "corrected_runs": 0,
            "groups": [],
        }

    finally:
        session.rollback()

        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()

        session.close()
