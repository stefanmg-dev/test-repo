import os
from datetime import datetime, timedelta, timezone

import pytest


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from database import SessionLocal
from database_models import ProcessingRun
from processing_run_service import ProcessingRunService


def make_run(
    service,
    *,
    filename,
    profile,
    status,
    requires_review,
    started_at,
):
    run = service.start_run(
        document_type="invoice",
        filename=filename,
        input_format="pdf",
        started_at=started_at,
    )
    return service.complete_run(
        run.id,
        processing_status=status,
        profile=profile,
        requires_review=requires_review,
        duration_ms=100,
        step_timings={"document_input_ms": 10},
        quality={
            "status": (
                "review" if requires_review else "accepted"
            ),
            "requires_review": requires_review,
            "warnings": [],
        },
        final_values={"filename": filename},
        collections={},
        validation={"valid": True, "errors": {}},
    )


def test_processing_run_history_queries_in_postgresql():
    session = SessionLocal()
    created_ids = []

    try:
        service = ProcessingRunService(session)
        now = datetime.now(timezone.utc)

        older = make_run(
            service,
            filename="history_older.pdf",
            profile="telecom_a1",
            status="accepted",
            requires_review=False,
            started_at=now - timedelta(seconds=2),
        )
        newer = make_run(
            service,
            filename="history_newer.pdf",
            profile="electricity_electrohold",
            status="review",
            requires_review=True,
            started_at=now - timedelta(seconds=1),
        )
        created_ids.extend([older.id, newer.id])

        detail = service.get_run(newer.id)
        assert detail.filename == "history_newer.pdf"
        assert detail.step_timings == {
            "document_input_ms": 10
        }

        items, total = service.list_runs(
            offset=0,
            limit=10,
            document_type="invoice",
            processing_status="review",
            profile="electricity_electrohold",
            requires_review=True,
        )

        matching_ids = [
            item.id for item in items if item.id in created_ids
        ]
        assert matching_ids == [newer.id]
        assert total >= 1

        unreviewed_items, unreviewed_total = (
            service.list_runs(
                offset=0,
                limit=100,
                document_type="invoice",
                processing_status="accepted",
                profile="telecom_a1",
                requires_review=False,
            )
        )
        assert older.id in {
            item.id for item in unreviewed_items
        }
        assert unreviewed_total >= 1

        unfiltered_items, unfiltered_total = (
            service.list_runs(
                offset=0,
                limit=100,
            )
        )
        created_in_order = [
            item.id
            for item in unfiltered_items
            if item.id in created_ids
        ]
        assert created_in_order == [newer.id, older.id]
        assert unfiltered_total >= 2
    finally:
        session.rollback()
        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()
        session.close()
