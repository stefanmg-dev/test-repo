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

    def get(self, run_id: UUID) -> ProcessingRun | None:
        return self._session.get(ProcessingRun, run_id)

    def list(
        self,
        *,
        offset: int,
        limit: int,
    ) -> list[ProcessingRun]:
        statement = (
            select(ProcessingRun)
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

    def count(self) -> int:
        statement = select(
            func.count(ProcessingRun.id)
        )
        return int(
            self._session.scalar(statement) or 0
        )
