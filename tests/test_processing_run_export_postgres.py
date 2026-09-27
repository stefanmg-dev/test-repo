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
from processing_run_service import ProcessingRunService


def test_export_runs_is_tenant_isolated():
    session = SessionLocal()
    tenant_id = f"export-{uuid4()}"
    other_tenant_id = f"export-other-{uuid4()}"
    created_ids = []

    try:
        service = ProcessingRunService(session)

        for tenant, filename in (
            (tenant_id, "included.pdf"),
            (other_tenant_id, "excluded.pdf"),
        ):
            run = service.start_run(
                document_type="invoice",
                filename=filename,
                input_format="pdf",
                tenant_id=tenant,
            )
            created_ids.append(run.id)

            service.complete_run(
                run.id,
                processing_status="accepted",
                profile="telecom_a1",
                requires_review=False,
                duration_ms=10,
                step_timings={},
                quality={
                    "status": "accepted",
                    "requires_review": False,
                },
                final_values={
                    "invoice_number": filename,
                },
                collections={},
                validation={},
                configuration_hash="export-hash",
            )

        exported = service.export_runs(
            tenant_id=tenant_id,
        )

        assert [run.filename for run in exported] == [
            "included.pdf"
        ]

    finally:
        session.rollback()

        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()

        session.close()
