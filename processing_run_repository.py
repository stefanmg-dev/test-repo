from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database_models import ProcessingRun


class ProcessingRunRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, processing_run: ProcessingRun) -> ProcessingRun:
        self._session.add(processing_run)
        self._session.flush()
        return processing_run

    def get(
        self,
        run_id: UUID,
        *,
        tenant_id: str | None = None,
    ) -> ProcessingRun | None:
        if tenant_id is None:
            return self._session.get(ProcessingRun, run_id)
        statement = select(ProcessingRun).where(
            ProcessingRun.id == run_id,
            ProcessingRun.tenant_id == tenant_id,
        )
        return self._session.scalar(statement)

    def list(
        self,
        *,
        offset: int,
        limit: int,
        document_type: str | None = None,
        processing_status: str | None = None,
        profile: str | None = None,
        requires_review: bool | None = None,
        tenant_id: str | None = None,
    ) -> list[ProcessingRun]:
        statement = select(ProcessingRun)
        statement = self._apply_filters(
            statement,
            document_type=document_type,
            processing_status=processing_status,
            profile=profile,
            requires_review=requires_review,
            tenant_id=tenant_id,
        )
        statement = (
            statement
            .order_by(
                ProcessingRun.created_at.desc(),
                ProcessingRun.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(
            self._session.scalars(statement).all()
        )

    def count(
        self,
        *,
        document_type: str | None = None,
        processing_status: str | None = None,
        profile: str | None = None,
        requires_review: bool | None = None,
        tenant_id: str | None = None,
    ) -> int:
        statement = select(
            func.count(ProcessingRun.id)
        )
        statement = self._apply_filters(
            statement,
            document_type=document_type,
            processing_status=processing_status,
            profile=profile,
            requires_review=requires_review,
            tenant_id=tenant_id,
        )
        return int(
            self._session.scalar(statement) or 0
        )

    @staticmethod
    def _apply_filters(
        statement,
        *,
        document_type: str | None,
        processing_status: str | None,
        profile: str | None,
        requires_review: bool | None,
        tenant_id: str | None,
    ):
        if tenant_id is not None:
            statement = statement.where(
                ProcessingRun.tenant_id == tenant_id
            )
        if document_type is not None:
            statement = statement.where(
                ProcessingRun.document_type == document_type
            )
        if processing_status is not None:
            statement = statement.where(
                ProcessingRun.processing_status
                == processing_status
            )
        if profile is not None:
            statement = statement.where(
                ProcessingRun.profile == profile
            )
        if requires_review is not None:
            statement = statement.where(
                ProcessingRun.requires_review
                == requires_review
            )
        return statement
