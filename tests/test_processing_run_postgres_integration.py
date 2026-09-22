import os
from datetime import datetime, timezone

import pytest


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from database import SessionLocal
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
