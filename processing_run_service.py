from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from database_models import ProcessingRun
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
        started_at: datetime | None = None,
    ) -> ProcessingRun:
        processing_run = ProcessingRun(
            document_type=document_type,
            filename=filename,
            input_format=input_format,
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
        completed_at: datetime | None = None,
    ) -> ProcessingRun:
        processing_run = self._get_required(run_id)
        processing_run.processing_status = processing_status
        processing_run.profile = profile
        processing_run.requires_review = requires_review
        processing_run.duration_ms = duration_ms
        processing_run.step_timings = step_timings
        processing_run.quality = quality
        processing_run.final_values = final_values
        processing_run.collections = collections
        processing_run.validation = validation
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

    def get_run(self, run_id: UUID) -> ProcessingRun:
        return self._get_required(run_id)

    def list_runs(
        self,
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[ProcessingRun], int]:
        return (
            self._repository.list(
                offset=offset,
                limit=limit,
            ),
            self._repository.count(),
        )

    def _get_required(self, run_id: UUID) -> ProcessingRun:
        processing_run = self._repository.get(run_id)
        if processing_run is None:
            raise ProcessingRunNotFoundError(
                f"Processing run '{run_id}' was not found"
            )
        return processing_run
