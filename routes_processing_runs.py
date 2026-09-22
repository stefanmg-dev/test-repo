from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from extraction_models import ApiErrorResponseModel
from processing_run_dependencies import (
    ProcessingRunServiceDependency,
)
from processing_run_models import (
    ProcessingRunDetailModel,
    ProcessingRunListResponseModel,
)
from processing_run_service import ProcessingRunNotFoundError


router = APIRouter(
    prefix="/api/v1/processing-runs",
    tags=["processing-runs"],
)


@router.get(
    "/{run_id}",
    response_model=ProcessingRunDetailModel,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Processing run was not found",
            "model": ApiErrorResponseModel,
        }
    },
)
def get_processing_run(
    run_id: UUID,
    processing_run_service: ProcessingRunServiceDependency,
):
    try:
        return processing_run_service.get_run(run_id)
    except ProcessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=ProcessingRunListResponseModel,
)
def list_processing_runs(
    processing_run_service: ProcessingRunServiceDependency,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items, total = processing_run_service.list_runs(
        offset=offset,
        limit=limit,
    )
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
