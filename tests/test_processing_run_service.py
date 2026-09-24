from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunService,
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
        completed_at=completed_at,
    )

    assert result is processing_run
    assert result.processing_status == "accepted"
    assert result.profile == "telecom_a1"
    assert result.duration_ms == 1250
    assert result.step_timings == {"document_input_ms": 10}
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
