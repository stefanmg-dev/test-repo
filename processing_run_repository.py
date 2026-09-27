from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from database_models import ProcessingRun


class ProcessingRunRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, processing_run: ProcessingRun) -> ProcessingRun:
        self._session.add(processing_run)
        self._session.flush()
        return processing_run

    def complete_review_atomic(
        self,
        run_id: UUID,
        *,
        tenant_id: str | None,
        status: str,
        reviewed_at,
        reviewed_by_type: str,
        reviewed_by_subject: str,
        comment: str | None,
        corrected_values,
    ) -> bool:
        statement = (
            update(ProcessingRun)
            .where(
                ProcessingRun.id == run_id,
                ProcessingRun.review_status == "pending",
            )
            .values(
                review_status=status,
                reviewed_at=reviewed_at,
                reviewed_by_type=reviewed_by_type,
                reviewed_by_subject=reviewed_by_subject,
                review_comment=comment,
                corrected_values=corrected_values,
            )
            .returning(ProcessingRun.id)
        )

        if tenant_id is not None:
            statement = statement.where(
                ProcessingRun.tenant_id == tenant_id
            )

        updated_id = self._session.execute(
            statement
        ).scalar_one_or_none()

        return updated_id is not None

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
        review_status: str | None = None,
        tenant_id: str | None = None,
    ) -> list[ProcessingRun]:
        statement = select(ProcessingRun)
        statement = self._apply_filters(
            statement,
            document_type=document_type,
            processing_status=processing_status,
            profile=profile,
            requires_review=requires_review,
            review_status=review_status,
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

    def review_summary(
        self,
        *,
        tenant_id: str | None = None,
    ) -> dict:
        review_duration_ms = (
            func.extract(
                "epoch",
                ProcessingRun.reviewed_at
                - ProcessingRun.completed_at,
            )
            * 1000
        )

        statement = select(
            func.count(ProcessingRun.id).label(
                "total_requiring_review"
            ),
            func.count(ProcessingRun.id)
            .filter(
                ProcessingRun.review_status == "pending"
            )
            .label("pending"),
            func.count(ProcessingRun.id)
            .filter(
                ProcessingRun.review_status == "approved"
            )
            .label("approved"),
            func.count(ProcessingRun.id)
            .filter(
                ProcessingRun.review_status == "corrected"
            )
            .label("corrected"),
            func.count(ProcessingRun.id)
            .filter(
                ProcessingRun.review_status == "rejected"
            )
            .label("rejected"),
            func.avg(review_duration_ms)
            .filter(
                ProcessingRun.reviewed_at.is_not(None),
                ProcessingRun.completed_at.is_not(None),
            )
            .label("average_review_duration_ms"),
        ).where(
            ProcessingRun.requires_review.is_(True)
        )

        if tenant_id is not None:
            statement = statement.where(
                ProcessingRun.tenant_id == tenant_id
            )

        row = self._session.execute(statement).one()

        return {
            "total_requiring_review": int(
                row.total_requiring_review or 0
            ),
            "pending": int(row.pending or 0),
            "approved": int(row.approved or 0),
            "corrected": int(row.corrected or 0),
            "rejected": int(row.rejected or 0),
            "average_review_duration_ms": (
                round(row.average_review_duration_ms)
                if row.average_review_duration_ms is not None
                else None
            ),
        }

    def count(
        self,
        *,
        document_type: str | None = None,
        processing_status: str | None = None,
        profile: str | None = None,
        requires_review: bool | None = None,
        review_status: str | None = None,
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
            review_status=review_status,
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
        review_status: str | None,
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
        if review_status is not None:
            statement = statement.where(
                ProcessingRun.review_status == review_status
            )
        return statement
