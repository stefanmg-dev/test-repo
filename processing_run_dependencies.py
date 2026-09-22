from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_database_session
from processing_run_service import ProcessingRunService


DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def get_processing_run_service(
    session: DatabaseSession,
) -> ProcessingRunService:
    return ProcessingRunService(session)


ProcessingRunServiceDependency = Annotated[
    ProcessingRunService,
    Depends(get_processing_run_service),
]
