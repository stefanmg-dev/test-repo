from unittest.mock import Mock
from uuid import uuid4

import pytest

from database_models import ProcessingRun
from processing_run_service import (
    ProcessingRunReviewError,
    ProcessingRunReviewService,
)


def pending_run():
    return ProcessingRun(
        id=uuid4(),
        document_type="invoice",
        filename="review.pdf",
        input_format="pdf",
        processing_status="review",
        requires_review=True,
        review_status="pending",
        final_values={"invoice_number": "ORIGINAL"},
    )


def service_with(run):
    session = Mock()
    session.get.return_value = run
    return ProcessingRunReviewService(session), session


@pytest.mark.parametrize("status", ["approved", "rejected"])
def test_completes_review_without_corrections(status):
    run = pending_run()
    service, session = service_with(run)

    result = service.review_run(
        run.id,
        status=status,
        reviewed_by_type="user",
        reviewed_by_subject="reviewer-1",
        comment="Reviewed",
    )

    assert result.review_status == status
    assert result.reviewed_by_type == "user"
    assert result.reviewed_by_subject == "reviewer-1"
    assert result.reviewed_at is not None
    assert result.review_comment == "Reviewed"
    assert result.corrected_values is None
    assert result.final_values == {
        "invoice_number": "ORIGINAL"
    }
    session.commit.assert_called_once_with()


def test_corrected_review_preserves_original_values():
    run = pending_run()
    service, _ = service_with(run)

    result = service.review_run(
        run.id,
        status="corrected",
        reviewed_by_type="user",
        reviewed_by_subject="reviewer-1",
        corrected_values={"invoice_number": "CORRECTED"},
    )

    assert result.final_values == {
        "invoice_number": "ORIGINAL"
    }
    assert result.corrected_values == {
        "invoice_number": "CORRECTED"
    }
    assert service.effective_values(result) == {
        "invoice_number": "CORRECTED"
    }


def test_rejected_review_has_no_effective_values():
    run = pending_run()
    service, _ = service_with(run)

    result = service.review_run(
        run.id,
        status="rejected",
        reviewed_by_type="user",
        reviewed_by_subject="reviewer-1",
    )

    assert service.effective_values(result) is None


def test_corrected_review_requires_corrected_values():
    run = pending_run()
    service, _ = service_with(run)

    with pytest.raises(
        ProcessingRunReviewError,
        match="corrected_values are required",
    ):
        service.review_run(
            run.id,
            status="corrected",
            reviewed_by_type="user",
            reviewed_by_subject="reviewer-1",
        )


def test_completed_review_cannot_be_changed():
    run = pending_run()
    run.review_status = "approved"
    service, _ = service_with(run)

    with pytest.raises(
        ProcessingRunReviewError,
        match="already completed",
    ):
        service.review_run(
            run.id,
            status="rejected",
            reviewed_by_type="user",
            reviewed_by_subject="reviewer-1",
        )
