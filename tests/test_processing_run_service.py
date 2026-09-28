from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunService,
    UniversalInvoiceUnavailableError,
)


def build_session():
    session = Mock()
    session.get.return_value = None
    return session


def test_starts_processing_run():
    session = build_session()
    service = ProcessingRunService(session)
    started_at = datetime(2026, 9, 22, tzinfo=timezone.utc)

    processing_run = service.start_run(
        document_type="invoice",
        filename="invoice.pdf",
        input_format="pdf",
        started_at=started_at,
    )

    assert processing_run.document_type == "invoice"
    assert processing_run.filename == "invoice.pdf"
    assert processing_run.input_format == "pdf"
    assert processing_run.processing_status == "processing"
    assert processing_run.requires_review is False
    assert processing_run.tenant_id == "default"
    assert processing_run.created_by_type == "system"
    assert processing_run.created_by_subject == "legacy"
    assert processing_run.started_at == started_at
    session.add.assert_called_once_with(processing_run)
    session.flush.assert_called_once_with()
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(processing_run)


def test_completes_processing_run():
    session = build_session()
    run_id = uuid4()
    processing_run = ProcessingRun(
        id=run_id,
        document_type="invoice",
        filename="invoice.pdf",
        input_format="pdf",
        processing_status="processing",
        requires_review=False,
    )
    session.get.return_value = processing_run
    service = ProcessingRunService(session)
    completed_at = datetime(2026, 9, 22, 0, 0, 1, tzinfo=timezone.utc)

    result = service.complete_run(
        run_id,
        processing_status="accepted",
        profile="telecom_a1",
        requires_review=False,
        duration_ms=1250,
        step_timings={"document_input_ms": 10},
        quality={"status": "accepted"},
        final_values={"invoice_number": "123"},
        collections={"items": []},
        validation={"valid": True, "errors": {}},
        invoice_schema_version="1",
        invoice_shadow_validation_status="failed",
        invoice_shadow_validation_reason="validation_error",
        completed_at=completed_at,
    )

    assert result is processing_run
    assert result.processing_status == "accepted"
    assert result.review_status is None
    assert result.profile == "telecom_a1"
    assert result.duration_ms == 1250
    assert result.step_timings == {"document_input_ms": 10}
    assert result.invoice_schema_version == "1"
    assert result.invoice_shadow_validation_status == "failed"
    assert result.invoice_shadow_validation_reason == (
        "validation_error"
    )
    assert result.completed_at == completed_at
    assert result.error is None
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(processing_run)


def test_marks_processing_run_as_failed():
    session = build_session()
    run_id = uuid4()
    processing_run = ProcessingRun(
        id=run_id,
        document_type="invoice",
        filename="broken.pdf",
        input_format="pdf",
        processing_status="processing",
        requires_review=False,
    )
    session.get.return_value = processing_run
    service = ProcessingRunService(session)

    result = service.fail_run(
        run_id,
        error={
            "code": "invalid_document",
            "detail": "Invalid or corrupted PDF file",
        },
        duration_ms=15,
        step_timings={"document_input_ms": 15},
    )

    assert result.processing_status == "failed"
    assert result.duration_ms == 15
    assert result.step_timings == {"document_input_ms": 15}
    assert result.error == {
        "code": "invalid_document",
        "detail": "Invalid or corrupted PDF file",
    }
    assert result.completed_at is not None
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(processing_run)


def test_requires_existing_processing_run():
    session = build_session()
    run_id = uuid4()
    service = ProcessingRunService(session)

    with pytest.raises(
        ProcessingRunNotFoundError,
        match=str(run_id),
    ):
        service.fail_run(
            run_id,
            error={"code": "failure"},
            duration_ms=1,
            step_timings={},
        )

    session.commit.assert_not_called()


def test_retention_preview_uses_configured_cutoff():
    session = build_session()
    service = ProcessingRunService(session)
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    expected_cutoff = now - timedelta(days=365)
    row = Mock(
        candidate_count=2,
        oldest_candidate_completed_at=(
            expected_cutoff - timedelta(days=10)
        ),
        newest_candidate_completed_at=(
            expected_cutoff - timedelta(seconds=1)
        ),
    )
    session.execute.return_value.one.return_value = row

    result = service.retention_preview(
        tenant_id="tenant-1",
        now=now,
    )

    assert result["retention_days"] == 365
    assert result["cutoff"] == expected_cutoff
    assert result["candidate_count"] == 2
    sql = str(session.execute.call_args.args[0])
    assert "processing_runs.completed_at" in sql
    assert "processing_runs.processing_status" in sql
    assert "processing_runs.review_status" in sql
    assert "processing_runs.tenant_id" in sql


def test_execute_retention_commits_bounded_delete():
    session = build_session()
    service = ProcessingRunService(session)
    now = datetime(2026, 9, 27, tzinfo=timezone.utc)
    expected_cutoff = now - timedelta(days=365)
    session.scalars.return_value.all.return_value = [
        uuid4(),
        uuid4(),
    ]

    result = service.execute_retention(
        limit=100,
        tenant_id="tenant-1",
        now=now,
    )

    assert result == {
        "retention_days": 365,
        "cutoff": expected_cutoff,
        "limit": 100,
        "deleted_count": 2,
    }
    sql = str(session.scalars.call_args.args[0])
    assert "DELETE FROM processing_runs" in sql
    assert "processing_runs.tenant_id" in sql
    assert "processing_runs.completed_at" in sql
    assert "processing_runs.review_status" in sql
    session.commit.assert_called_once_with()

def test_universal_invoice_rejects_non_invoice_run():
    session = build_session()
    run = ProcessingRun(
        id=uuid4(),
        document_type="receipt",
        filename="receipt.pdf",
        input_format="pdf",
        processing_status="accepted",
        requires_review=False,
    )
    session.get.return_value = run

    with pytest.raises(
        UniversalInvoiceUnavailableError,
        match="only for invoice runs",
    ):
        ProcessingRunService(session).get_universal_invoice(run.id)


def test_universal_invoice_maps_persisted_values():
    session = build_session()
    run = ProcessingRun(
        id=uuid4(),
        document_type="invoice",
        filename="invoice.pdf",
        input_format="pdf",
        processing_status="accepted",
        requires_review=False,
        final_values={"invoice_number": "INV-1"},
        collections={},
    )
    session.get.return_value = run

    invoice = ProcessingRunService(session).get_universal_invoice(run.id)

    assert invoice.schema_version == "1"
    assert invoice.invoice_number == "INV-1"
