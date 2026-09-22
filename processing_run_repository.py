from uuid import UUID

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
