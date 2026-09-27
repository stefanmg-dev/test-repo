from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from database_models import ProcessingRun
from extraction_quality_analysis import (
    aggregate_quality_analysis,
)
from processing_run_repository import ProcessingRunRepository


class ProcessingRunNotFoundError(LookupError):
    pass


class ProcessingRunService:
    def __init__(self, session: Session):
        self._session = session
        self._repository = ProcessingRunRepository(session)

    def start_run(
        self,
        *,
        document_type: str,
        filename: str,
        input_format: str,
        tenant_id: str = "default",
        created_by_type: str = "system",
        created_by_subject: str = "legacy",
        started_at: datetime | None = None,
    ) -> ProcessingRun:
        processing_run = ProcessingRun(
            document_type=document_type,
            filename=filename,
            input_format=input_format,
            tenant_id=tenant_id,
            created_by_type=created_by_type,
            created_by_subject=created_by_subject,
            processing_status="processing",
            requires_review=False,
            started_at=started_at or datetime.now(timezone.utc),
        )
        self._repository.add(processing_run)
        self._session.commit()
        self._session.refresh(processing_run)
        return processing_run

    def complete_run(
        self,
        run_id: UUID,
        *,
        processing_status: str,
        profile: str | None,
        requires_review: bool,
        duration_ms: int,
        step_timings: dict[str, int],
        quality: dict[str, Any],
        final_values: dict[str, Any],
        collections: dict[str, Any],
        validation: dict[str, Any],
        configuration_hash: str | None = None,
        configuration_snapshot: dict[str, Any] | None = None,
        configuration_schema_version: str | None = None,
        completed_at: datetime | None = None,
    ) -> ProcessingRun:
        processing_run = self._get_required(run_id)
        processing_run.processing_status = processing_status
        processing_run.profile = profile
        processing_run.requires_review = requires_review
        processing_run.review_status = (
            "pending" if requires_review else None
        )
        processing_run.duration_ms = duration_ms
        processing_run.step_timings = step_timings
        processing_run.quality = quality
        processing_run.final_values = final_values
        processing_run.collections = collections
        processing_run.validation = validation
        processing_run.configuration_hash = configuration_hash
        processing_run.configuration_snapshot = (
            configuration_snapshot
        )
        processing_run.configuration_schema_version = (
            configuration_schema_version
        )
        processing_run.error = None
        processing_run.completed_at = (
            completed_at or datetime.now(timezone.utc)
        )
        self._session.commit()
        self._session.refresh(processing_run)
        return processing_run

    def fail_run(
        self,
        run_id: UUID,
        *,
        error: dict[str, Any],
        duration_ms: int,
        step_timings: dict[str, int],
        completed_at: datetime | None = None,
    ) -> ProcessingRun:
        processing_run = self._get_required(run_id)
        processing_run.processing_status = "failed"
        processing_run.duration_ms = duration_ms
        processing_run.step_timings = step_timings
        processing_run.error = error
        processing_run.completed_at = (
            completed_at or datetime.now(timezone.utc)
        )
        self._session.commit()
        self._session.refresh(processing_run)
        return processing_run

    def get_run(
        self,
        run_id: UUID,
        *,
        tenant_id: str | None = None,
    ) -> ProcessingRun:
        return self._get_required(
            run_id,
            tenant_id=tenant_id,
        )

    def export_runs(
        self,
        tenant_id=None,
    ):
        return self._repository.list_export_runs(
            tenant_id=tenant_id,
        )

    def extraction_quality_analysis(
        self,
        tenant_id: str | None = None,
    ) -> dict:
        runs = self._repository.list_corrected_reviews(
            tenant_id=tenant_id,
        )

        records = [
            {
                "document_type": run.document_type,
                "profile": run.profile,
                "configuration_hash": run.configuration_hash,
                "original_values": run.final_values,
                "corrected_values": run.corrected_values,
            }
            for run in runs
        ]

        return aggregate_quality_analysis(records)

    def review_summary(
        self,
        *,
        tenant_id: str | None = None,
    ) -> dict:
        return self._repository.review_summary(
            tenant_id=tenant_id,
        )

    def list_runs(
        self,
        *,
        offset: int,
        limit: int,
        document_type: str | None = None,
        processing_status: str | None = None,
        profile: str | None = None,
        requires_review: bool | None = None,
        review_status: str | None = None,
        tenant_id: str | None = None,
    ) -> tuple[list[ProcessingRun], int]:
        filters = {
            "document_type": document_type,
            "processing_status": processing_status,
            "profile": profile,
            "requires_review": requires_review,
            "review_status": review_status,
            "tenant_id": tenant_id,
        }
        return (
            self._repository.list(
                offset=offset,
                limit=limit,
                **filters,
            ),
            self._repository.count(**filters),
        )

    def _get_required(
        self,
        run_id: UUID,
        *,
        tenant_id: str | None = None,
    ) -> ProcessingRun:
        processing_run = self._repository.get(
            run_id,
            tenant_id=tenant_id,
        )
        if processing_run is None:
            raise ProcessingRunNotFoundError(
                f"Processing run '{run_id}' was not found"
            )
        return processing_run


class ProcessingRunReviewError(ValueError):
    pass


class ProcessingRunReviewService:
    ALLOWED_STATUSES = frozenset({
        "approved",
        "corrected",
        "rejected",
    })

    def __init__(self, session: Session):
        self._session = session
        self._repository = ProcessingRunRepository(session)

    def get_review_run(
        self,
        run_id: UUID,
        *,
        tenant_id: str | None = None,
    ) -> ProcessingRun:
        processing_run = self._repository.get(
            run_id,
            tenant_id=tenant_id,
        )
        if processing_run is None:
            raise ProcessingRunNotFoundError(
                f"Processing run '{run_id}' was not found"
            )
        return processing_run

    def review_run(
        self,
        run_id: UUID,
        *,
        status: str,
        reviewed_by_type: str,
        reviewed_by_subject: str,
        tenant_id: str | None = None,
        corrected_values: dict[str, Any] | None = None,
        comment: str | None = None,
        reviewed_at: datetime | None = None,
    ) -> ProcessingRun:
        processing_run = self._repository.get(
            run_id,
            tenant_id=tenant_id,
        )
        if processing_run is None:
            raise ProcessingRunNotFoundError(
                f"Processing run '{run_id}' was not found"
            )
        if not processing_run.requires_review:
            raise ProcessingRunReviewError(
                "Processing run does not require review"
            )
        if processing_run.review_status != "pending":
            raise ProcessingRunReviewError(
                "Processing run review is already completed"
            )
        if status not in self.ALLOWED_STATUSES:
            raise ProcessingRunReviewError(
                f"Unsupported review status: {status}"
            )
        if status == "corrected" and corrected_values is None:
            raise ProcessingRunReviewError(
                "corrected_values are required for corrected review"
            )
        if status != "corrected" and corrected_values is not None:
            raise ProcessingRunReviewError(
                "corrected_values are allowed only for corrected review"
            )

        decision_time = (
            reviewed_at or datetime.now(timezone.utc)
        )

        updated = self._repository.complete_review_atomic(
            run_id,
            tenant_id=tenant_id,
            status=status,
            reviewed_at=decision_time,
            reviewed_by_type=reviewed_by_type,
            reviewed_by_subject=reviewed_by_subject,
            comment=comment,
            corrected_values=corrected_values,
        )

        if not updated:
            self._session.rollback()
            raise ProcessingRunReviewError(
                "Processing run review is already completed"
            )

        processing_run.review_status = status
        processing_run.reviewed_at = decision_time
        processing_run.reviewed_by_type = reviewed_by_type
        processing_run.reviewed_by_subject = reviewed_by_subject
        processing_run.review_comment = comment
        processing_run.corrected_values = corrected_values

        self._session.commit()
        self._session.refresh(processing_run)
        return processing_run

    @staticmethod
    def effective_values(
        processing_run: ProcessingRun,
    ) -> dict[str, Any] | None:
        if processing_run.review_status == "rejected":
            return None
        if processing_run.review_status == "corrected":
            return processing_run.corrected_values
        return processing_run.final_values
