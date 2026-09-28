import os
from datetime import datetime, timezone
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

def test_universal_invoice_feedback_export_is_tenant_scoped():
    session = SessionLocal()
    tenant_id = f"feedback-{uuid4()}"
    other_tenant_id = f"feedback-other-{uuid4()}"
    created_ids = []

    def add_run(tenant, status, filename):
        run = ProcessingRun(
            tenant_id=tenant,
            document_type="invoice",
            filename=filename,
            input_format="pdf",
            processing_status="review",
            requires_review=True,
            review_status=status,
            reviewed_at=datetime.now(timezone.utc),
            reviewed_by_type="user",
            final_values={"invoice_number": filename},
            corrected_values=(
                {"invoice_number": f"corrected-{filename}"}
                if status == "corrected"
                else None
            ),
            collections={},
            invoice_schema_version="1",
            configuration_hash="feedback-hash",
            invoice_shadow_validation_status="succeeded",
        )
        session.add(run)
        session.flush()
        created_ids.append(run.id)
        return run

    try:
        approved = add_run(tenant_id, "approved", "approved.pdf")
        corrected = add_run(tenant_id, "corrected", "corrected.pdf")
        add_run(tenant_id, "rejected", "rejected.pdf")
        add_run(other_tenant_id, "corrected", "other.pdf")
        session.commit()

        exported = (
            ProcessingRunService(session)
            .export_universal_invoice_feedback(tenant_id=tenant_id)
        )

        lines = exported.splitlines()

        assert len(lines) == 2
        assert str(approved.id) in lines[0]
        assert str(corrected.id) in lines[1]
        assert "rejected.pdf" not in exported
        assert "other.pdf" not in exported
    finally:
        session.rollback()
        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()
        session.close()

def test_feedback_export_excludes_unsuccessful_shadow_runs():
    session = SessionLocal()
    tenant_id = f"feedback-shadow-{uuid4()}"
    created_ids = []
    try:
        run = ProcessingRun(
            tenant_id=tenant_id,
            document_type="invoice",
            filename="failed-shadow.pdf",
            input_format="pdf",
            processing_status="review",
            requires_review=True,
            review_status="approved",
            reviewed_at=datetime.now(timezone.utc),
            reviewed_by_type="user",
            final_values={"invoice_number": "INV-1"},
            collections={},
            invoice_schema_version="1",
            invoice_shadow_validation_status="failed",
        )
        session.add(run)
        session.commit()
        created_ids.append(run.id)

        content = ProcessingRunService(
            session
        ).export_universal_invoice_feedback(tenant_id=tenant_id)

        assert content == ""
    finally:
        session.rollback()
        if created_ids:
            session.query(ProcessingRun).filter(
                ProcessingRun.id.in_(created_ids)
            ).delete(synchronize_session=False)
            session.commit()
        session.close()
