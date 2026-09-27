import os
from datetime import datetime, timedelta, timezone

import pytest
from uuid import uuid4


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from database import SessionLocal
from database_models import ProcessingRun
from processing_run_service import ProcessingRunService


def test_processing_run_lifecycle_in_postgresql():
    session = SessionLocal()
    processing_run = None

    try:
        service = ProcessingRunService(session)
        started_at = datetime.now(timezone.utc)

        processing_run = service.start_run(
            document_type="invoice",
            filename="postgres_integration_test.pdf",
            input_format="pdf",
            started_at=started_at,
        )

        run_id = processing_run.id
        session.expunge_all()

        completed = service.complete_run(
            run_id,
            processing_status="review",
            profile="telecom_a1",
            requires_review=True,
            duration_ms=321,
            step_timings={
                "document_input_ms": 120,
                "document_engine_ms": 80,
            },
            quality={
                "status": "review",
                "requires_review": True,
                "warnings": [
                    {
                        "code": "integration_test",
                        "message": "PostgreSQL JSONB round trip",
                    }
                ],
            },
            final_values={
                "invoice_number": "TEST-123",
                "total_amount": "42.00",
            },
            collections={
                "items": [
                    {
                        "name": "test_item",
                        "amount": "42.00",
                    }
                ]
            },
            validation={
                "valid": True,
                "errors": {},
            },
        )

        assert completed.id == run_id
        assert completed.processing_status == "review"
        assert completed.profile == "telecom_a1"
        assert completed.requires_review is True
        assert completed.duration_ms == 321
        assert completed.step_timings == {
            "document_input_ms": 120,
            "document_engine_ms": 80,
        }
        assert completed.quality["warnings"][0]["code"] == (
            "integration_test"
        )
        assert completed.final_values["invoice_number"] == (
            "TEST-123"
        )
        assert completed.collections["items"][0]["amount"] == (
            "42.00"
        )
        assert completed.validation == {
            "valid": True,
            "errors": {},
        }
        assert completed.completed_at is not None

        session.expunge_all()
        reloaded = session.get(type(completed), run_id)

        assert reloaded is not None
        assert reloaded.processing_status == "review"
        assert reloaded.step_timings == {
            "document_input_ms": 120,
            "document_engine_ms": 80,
        }
        assert reloaded.final_values == {
            "invoice_number": "TEST-123",
            "total_amount": "42.00",
        }
        assert reloaded.error is None
    finally:
        session.rollback()
        if processing_run is not None:
            persisted = session.get(
                type(processing_run),
                processing_run.id,
            )
            if persisted is not None:
                session.delete(persisted)
                session.commit()
        session.close()


def test_retention_preview_filters_candidates_in_postgresql():
    session = SessionLocal()
    tenant_id = f"retention-{uuid4()}"
    other_tenant_id = f"retention-other-{uuid4()}"
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    cutoff = now - timedelta(days=365)
    created_ids = []

    def add_run(
        *,
        tenant,
        filename,
        processing_status,
        completed_at,
        requires_review=False,
        review_status=None,
    ):
        run = ProcessingRun(
            tenant_id=tenant,
            document_type="invoice",
            filename=filename,
            input_format="pdf",
            processing_status=processing_status,
            requires_review=requires_review,
            review_status=review_status,
            started_at=completed_at or now,
            completed_at=completed_at,
        )
        session.add(run)
        session.flush()
        created_ids.append(run.id)
        return run

    try:
        oldest = add_run(
            tenant=tenant_id,
            filename="oldest-candidate.pdf",
            processing_status="accepted",
            completed_at=cutoff - timedelta(days=20),
        )
        newest = add_run(
            tenant=tenant_id,
            filename="newest-candidate.pdf",
            processing_status="review",
            completed_at=cutoff - timedelta(seconds=1),
            requires_review=True,
            review_status="approved",
        )
        add_run(
            tenant=tenant_id,
            filename="pending-review.pdf",
            processing_status="review",
            completed_at=cutoff - timedelta(days=10),
            requires_review=True,
            review_status="pending",
        )
        add_run(
            tenant=tenant_id,
            filename="still-processing.pdf",
            processing_status="processing",
            completed_at=cutoff - timedelta(days=10),
        )
        add_run(
            tenant=tenant_id,
            filename="at-cutoff.pdf",
            processing_status="accepted",
            completed_at=cutoff,
        )
        add_run(
            tenant=tenant_id,
            filename="recent.pdf",
            processing_status="accepted",
            completed_at=cutoff + timedelta(seconds=1),
        )
        add_run(
            tenant=other_tenant_id,
            filename="other-tenant.pdf",
            processing_status="accepted",
            completed_at=cutoff - timedelta(days=30),
        )
        session.commit()

        preview = ProcessingRunService(session).retention_preview(
            tenant_id=tenant_id,
            now=now,
        )

        assert preview["retention_days"] == 365
        assert preview["cutoff"] == cutoff
        assert preview["candidate_count"] == 2
        assert preview["oldest_candidate_completed_at"] == (
            oldest.completed_at
        )
        assert preview["newest_candidate_completed_at"] == (
            newest.completed_at
        )
    finally:
        session.rollback()
        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()
        session.close()
