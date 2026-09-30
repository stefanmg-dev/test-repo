from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response, StreamingResponse

from extraction_models import ApiErrorResponseModel
from invoice_models import UniversalInvoiceModel
from processing_run_export import (
    stream_processing_runs_csv,
)
from processing_run_dependencies import (
    ProcessingRunServiceDependency,
    ProcessingRunReviewServiceDependency,
)
from processing_run_models import (
    InvoiceShadowSummaryModel,
    ExtractionQualityAnalysisModel,
    ProcessingRunDetailModel,
    ProcessingRunListResponseModel,
    ProcessingRunRetentionPreviewModel,
    ProcessingRunRetentionExecuteModel,
    ProcessingRunRetentionExecuteRequestModel,
    ProcessingRunReviewModel,
    ProcessingRunReviewRequestModel,
    ProcessingRunReviewSummaryModel,
)
from processing_run_service import (
    ProcessingRunNotFoundError,
    ProcessingRunReviewError,
    UniversalInvoiceUnavailableError,
    UniversalInvoiceFeedbackExportError,
    ProcessingRunReviewService,
)
from security_dependencies import (
    OptionalApiKeyPrincipal,
    require_scope,
)
from security_audit import audit_security_event
from security_principal import SecurityPrincipal
from security_scopes import (
    ADMIN,
    PROCESSING_RUNS_READ,
    PROCESSING_RUNS_REVIEW,
    enforce_scope_if_authenticated,
)


router = APIRouter(
    prefix="/api/v1/processing-runs",
    tags=["processing-runs"],
)


@router.get(
    "/export",
    summary="Export processing runs as CSV",
    description=(
        "Streams a tenant-scoped CSV snapshot of processing-run lifecycle, "
        "review, configuration, filename, and effective-value metadata. "
        "The export excludes raw OCR text. Authenticated requests require "
        "the processing-runs:read scope."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Processing runs CSV export",
            "content": {"text/csv": {}},
        }
    },
)
def export_processing_runs(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )

    tenant_id = (
        principal.tenant_id
        if principal is not None
        else "default"
    )

    processing_runs = processing_run_service.export_runs(
        tenant_id=tenant_id,
    )

    return StreamingResponse(
        stream_processing_runs_csv(processing_runs),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                'attachment; filename="processing-runs.csv"'
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get(
    "/universal-invoice-feedback-export",
    summary="Export reviewed Universal Invoice feedback as JSONL",
    description=(
        "Returns a deterministic tenant-scoped JSONL page of reviewed "
        "invoice feedback with original and reviewed Universal Invoice "
        "representations and review/configuration metadata. The export "
        "excludes filenames and raw OCR text. Resume with both next-cursor "
        "headers. Authenticated requests require the processing-runs:read "
        "scope."
    ),
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Universal Invoice feedback JSONL export page",
            "headers": {
                "X-Next-Reviewed-At": {
                    "description": (
                        "First component of the next-page cursor; omitted "
                        "on the final page."
                    ),
                    "schema": {"type": "string", "format": "date-time"},
                },
                "X-Next-Processing-Run-Id": {
                    "description": (
                        "Second component of the next-page cursor; omitted "
                        "on the final page."
                    ),
                    "schema": {"type": "string", "format": "uuid"},
                },
            },
            "content": {"application/x-ndjson": {}},
        },
        status.HTTP_409_CONFLICT: {
            "description": "Feedback export mapping failed atomically",
            "model": ApiErrorResponseModel,
        },
    },
)
def export_universal_invoice_feedback(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=1000,
            description="Required page size from 1 to 1000 records.",
        ),
    ],
    after_reviewed_at: Annotated[
        datetime | None,
        Query(
            description=(
                "First component of the exclusive tuple cursor. Supply "
                "together with after_processing_run_id."
            )
        ),
    ] = None,
    after_processing_run_id: Annotated[
        UUID | None,
        Query(
            description=(
                "Second component of the exclusive tuple cursor. Supply "
                "together with after_reviewed_at."
            )
        ),
    ] = None,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
    if (after_reviewed_at is None) != (
        after_processing_run_id is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "after_reviewed_at and after_processing_run_id "
                "must be provided together"
            ),
        )
    tenant_id = (
        principal.tenant_id
        if principal is not None
        else "default"
    )
    try:
        content, next_reviewed_at, next_run_id = (
            processing_run_service.export_universal_invoice_feedback(
                limit=limit,
                after_reviewed_at=after_reviewed_at,
                after_processing_run_id=after_processing_run_id,
                tenant_id=tenant_id,
            )
        )
    except UniversalInvoiceFeedbackExportError as exc:
        audit_security_event(
            "security.processing_invoice_feedback_export_failed",
            message="Universal Invoice feedback export failed",
            result="failure",
            principal=principal,
            feedback_export_limit=limit,
            cursor_supplied=after_reviewed_at is not None,
            feedback_export_outcome="error",
            failure_reason="mapping_error",
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    exported_count = content.count("\n")
    next_cursor_available = next_reviewed_at is not None
    if exported_count == 0:
        feedback_export_outcome = "empty"
    elif next_cursor_available:
        feedback_export_outcome = "continued"
    else:
        feedback_export_outcome = "final_page"
    audit_security_event(
        "security.processing_invoice_feedback_exported",
        message="Universal Invoice feedback exported",
        result="success",
        principal=principal,
        feedback_export_limit=limit,
        cursor_supplied=after_reviewed_at is not None,
        exported_count=exported_count,
        next_cursor_available=next_cursor_available,
        feedback_export_outcome=feedback_export_outcome,
    )
    headers = {
        "Content-Disposition": (
            "attachment; "
            'filename="universal-invoice-feedback.jsonl"'
        ),
        "X-Content-Type-Options": "nosniff",
    }
    if next_reviewed_at is not None and next_run_id is not None:
        headers["X-Next-Reviewed-At"] = next_reviewed_at.isoformat()
        headers["X-Next-Processing-Run-Id"] = str(next_run_id)
    return Response(
        content=content,
        media_type="application/x-ndjson",
        headers=headers,
    )


@router.get(
    "/extraction-quality",
    summary="Analyze reviewed extraction quality",
    description=(
        "Aggregates tenant-owned corrected runs by document type, profile, "
        "and configuration hash to show correction counts and rates. "
        "Requires the processing-runs:read scope when authenticated."
    ),
    response_description="Reviewed extraction quality analysis.",
    response_model=ExtractionQualityAnalysisModel,
)
def get_extraction_quality_analysis(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
    return processing_run_service.extraction_quality_analysis(
        tenant_id=(
            principal.tenant_id
            if principal is not None
            else "default"
        ),
    )


@router.get(
    "/invoice-shadow-summary",
    summary="Summarize Universal Invoice shadow validation",
    description=(
        "Returns tenant-owned shadow-validation totals, success rate, schema "
        "version breakdown, and safe failure reason counts without document "
        "values. Requires the processing-runs:read scope when authenticated."
    ),
    response_description="Universal Invoice shadow-validation summary.",
    response_model=InvoiceShadowSummaryModel,
)
def get_invoice_shadow_summary(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
    return processing_run_service.invoice_shadow_summary(
        tenant_id=(
            principal.tenant_id
            if principal is not None
            else "default"
        ),
    )


@router.get(
    "/review-summary",
    summary="Summarize processing run reviews",
    description=(
        "Returns tenant-owned review workflow counts and average completed "
        "review duration. Requires the processing-runs:read scope when "
        "authenticated."
    ),
    response_description="Processing review workflow summary.",
    response_model=ProcessingRunReviewSummaryModel,
)
def get_processing_run_review_summary(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
    return processing_run_service.review_summary(
        tenant_id=(
            principal.tenant_id
            if principal is not None
            else "default"
        ),
    )


@router.get(
    "/retention-preview",
    summary="Preview processing run retention",
    description=(
        "Returns the tenant-owned completed runs eligible for retention "
        "deletion under the configured cutoff. This read-only operation "
        "requires authentication and the internal admin scope."
    ),
    response_description="Tenant-scoped retention eligibility preview.",
    response_model=ProcessingRunRetentionPreviewModel,
)
def get_processing_run_retention_preview(
    processing_run_service: ProcessingRunServiceDependency,
    principal: Annotated[
        SecurityPrincipal,
        Depends(require_scope(ADMIN)),
    ],
):
    return processing_run_service.retention_preview(
        tenant_id=principal.tenant_id,
    )


@router.post(
    "/retention-execute",
    summary="Execute processing run retention",
    description=(
        "Atomically deletes a bounded number of tenant-owned completed runs "
        "older than the configured cutoff. Requires authentication, the "
        "internal admin scope, and exact DELETE confirmation."
    ),
    response_description="Retention cutoff and atomic deletion result.",
    response_model=ProcessingRunRetentionExecuteModel,
)
def execute_processing_run_retention(
    request: ProcessingRunRetentionExecuteRequestModel,
    processing_run_service: ProcessingRunServiceDependency,
    principal: Annotated[
        SecurityPrincipal,
        Depends(require_scope(ADMIN)),
    ],
):
    result = processing_run_service.execute_retention(
        limit=request.limit,
        tenant_id=principal.tenant_id,
    )
    audit_security_event(
        "security.processing_retention_executed",
        message="Processing run retention executed",
        result="success",
        principal=principal,
        retention_cutoff=result["cutoff"],
        retention_limit=result["limit"],
        deleted_count=result["deleted_count"],
    )
    return result


@router.get(
    "/{run_id}/universal-invoice",
    summary="Get Universal Invoice preview",
    description=(
        "Maps the persisted final values and collections of one tenant-owned "
        "invoice processing run to the versioned Universal Invoice schema. "
        "The operation is read-only and requires the processing-runs:read "
        "scope when authenticated. Nullable scalar fields indicate that the "
        "source run did not provide the corresponding value."
    ),
    response_description="Versioned Universal Invoice preview.",
    response_model=UniversalInvoiceModel,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Processing run was not found",
            "model": ApiErrorResponseModel,
        },
        status.HTTP_409_CONFLICT: {
            "description": "Universal invoice is unavailable",
            "model": ApiErrorResponseModel,
        },
    },
)
def get_processing_run_universal_invoice(
    run_id: Annotated[
        UUID,
        Path(
            description=(
                "Unique identifier of the invoice processing run to preview."
            )
        ),
    ],
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
    tenant_id = (
        principal.tenant_id
        if principal is not None
        else "default"
    )
    try:
        return processing_run_service.get_universal_invoice(
            run_id,
            tenant_id=tenant_id,
        )
    except ProcessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UniversalInvoiceUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "/{run_id}",
    summary="Get processing run details",
    description=(
        "Returns the tenant-owned processing run identified by run_id, "
        "including persisted extraction, validation, review, timing, "
        "configuration, and safe failure metadata. Authenticated requests "
        "require the processing-runs:read scope."
    ),
    response_description="Detailed processing run metadata.",
    response_model=ProcessingRunDetailModel,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Processing run was not found",
            "model": ApiErrorResponseModel,
        }
    },
)
def get_processing_run(
    run_id: Annotated[
        UUID,
        Path(
            description="Unique identifier of the processing run to retrieve."
        ),
    ],
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
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
    summary="List processing runs",
    description=(
        "Returns a bounded offset-based page of processing runs owned by "
        "the authenticated tenant. Optional filters are combined with AND "
        "semantics. List items intentionally omit extracted document values. "
        "Authenticated requests require the processing-runs:read scope."
    ),
    response_description="Paginated processing run summaries.",
    response_model=ProcessingRunListResponseModel,
)
def list_processing_runs(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
    offset: Annotated[int, Query(ge=0, description="Number of matching runs to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum page size from 1 to 100.")] = 20,
    document_type: Annotated[
        str | None,
        Query(min_length=1, max_length=100, description="Filter by configured document type."),
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
        Query(description="Filter by processing lifecycle status."),
    ] = None,
    profile: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
            pattern=r"^[a-z][a-z0-9_]*$",
            description="Filter by resolved supplier profile.",
        ),
    ] = None,
    requires_review: Annotated[
        bool | None,
        Query(description="Filter by human-review requirement."),
    ] = None,
    review_status: Annotated[
        Literal[
            "pending",
            "approved",
            "corrected",
            "rejected",
        ]
        | None,
        Query(description="Filter by review workflow state."),
    ] = None,
    invoice_shadow_validation_status: Annotated[
        Literal[
            "succeeded",
            "failed",
            "not_applicable",
        ]
        | None,
        Query(description="Filter by Universal Invoice shadow-validation status."),
    ] = None,
    invoice_schema_version: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=20,
            pattern=r"^[A-Za-z0-9._-]+$",
            description="Filter by Universal Invoice schema version.",
        ),
    ] = None,
):
    enforce_scope_if_authenticated(
        principal,
        PROCESSING_RUNS_READ,
    )
    items, total = processing_run_service.list_runs(
        offset=offset,
        limit=limit,
        document_type=document_type,
        processing_status=processing_status,
        profile=profile,
        requires_review=requires_review,
        review_status=review_status,
        invoice_shadow_validation_status=(
            invoice_shadow_validation_status
        ),
        invoice_schema_version=invoice_schema_version,
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


def review_response(processing_run):
    return {
        "processing_run_id": processing_run.id,
        "status": processing_run.review_status,
        "original_values": processing_run.final_values,
        "corrected_values": processing_run.corrected_values,
        "effective_values": (
            ProcessingRunReviewService.effective_values(
                processing_run
            )
        ),
        "comment": processing_run.review_comment,
        "reviewed_at": processing_run.reviewed_at,
        "reviewed_by_type": processing_run.reviewed_by_type,
        "reviewed_by_subject": (
            processing_run.reviewed_by_subject
        ),
    }


@router.get(
    "/{run_id}/review",
    summary="Get processing run review",
    description=(
        "Returns the tenant-owned review record and effective values for a "
        "processing run. Requires the processing-runs:review scope."
    ),
    response_description="Processing run review state and effective values.",
    response_model=ProcessingRunReviewModel,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Processing run was not found",
            "model": ApiErrorResponseModel,
        }
    },
)
def get_processing_run_review(
    run_id: Annotated[
        UUID,
        Path(description="Unique identifier of the processing run to review."),
    ],
    service: ProcessingRunReviewServiceDependency,
    principal: Annotated[
        SecurityPrincipal,
        Depends(require_scope(PROCESSING_RUNS_REVIEW)),
    ],
):
    try:
        processing_run = service.get_review_run(
            run_id,
            tenant_id=principal.tenant_id,
        )
        return review_response(processing_run)
    except ProcessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.put(
    "/{run_id}/review",
    summary="Record a processing run review decision",
    description=(
        "Records one terminal review decision for a tenant-owned processing "
        "run and preserves the original extraction values for audit. "
        "Requires the processing-runs:review scope."
    ),
    response_description="Recorded review decision and effective values.",
    response_model=ProcessingRunReviewModel,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Processing run was not found",
            "model": ApiErrorResponseModel,
        },
        status.HTTP_409_CONFLICT: {
            "description": "Review decision conflicts with the run state",
            "model": ApiErrorResponseModel,
        },
    },
)
def update_processing_run_review(
    run_id: Annotated[
        UUID,
        Path(description="Unique identifier of the processing run to review."),
    ],
    request: ProcessingRunReviewRequestModel,
    service: ProcessingRunReviewServiceDependency,
    principal: Annotated[
        SecurityPrincipal,
        Depends(require_scope(PROCESSING_RUNS_REVIEW)),
    ],
):
    try:
        processing_run = service.review_run(
            run_id,
            status=request.status,
            reviewed_by_type=principal.principal_type,
            reviewed_by_subject=principal.subject,
            tenant_id=principal.tenant_id,
            corrected_values=request.corrected_values,
            comment=request.comment,
        )
        audit_security_event(
            f"security.processing_review_{request.status}",
            message="Processing review decision recorded",
            result="success",
            principal=principal,
            processing_run_id=run_id,
            review_decision=request.status,
        )
        return review_response(processing_run)
    except ProcessingRunNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ProcessingRunReviewError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
