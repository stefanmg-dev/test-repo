from typing import Annotated, Literal
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
from security_dependencies import OptionalApiKeyPrincipal


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
    principal: OptionalApiKeyPrincipal,
):
    try:
        return processing_run_service.get_run(
            run_id,
            tenant_id=(
                principal.tenant_id
                if principal is not None
                else "default"
            ),
        )
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
    principal: OptionalApiKeyPrincipal,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    document_type: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    processing_status: Annotated[
        Literal[
            "processing",
            "accepted",
            "review",
            "invalid",
            "failed",
        ]
        | None,
        Query(),
    ] = None,
    profile: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            pattern=r"^[a-z][a-z0-9_]*$",
        ),
    ] = None,
    requires_review: bool | None = None,
):
    items, total = processing_run_service.list_runs(
        offset=offset,
        limit=limit,
        document_type=document_type,
        processing_status=processing_status,
        profile=profile,
        requires_review=requires_review,
        tenant_id=(
            principal.tenant_id
            if principal is not None
            else "default"
        ),
    )
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
    }
