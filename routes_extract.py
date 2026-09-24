import logging
from pathlib import Path
from time import perf_counter

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from config_store import load_config
from document_status import is_document_type_ready
from extraction_models import (
    ApiErrorResponseModel,
    DocumentInputErrorResponseModel,
    ExtractionResponseModel,
    RequestValidationErrorResponseModel,
)
from extraction_orchestrator import extract_document_data
from llm_engine import extract_values
from ocr_engine import (
    InvalidDocumentInputError,
    PayloadTooLargeError,
    UnsupportedFileTypeError,
    extract_document_input,
    extract_text,
)
from processing_run_dependencies import (
    ProcessingRunServiceDependency,
)
from request_context import set_processing_run_id
from security_dependencies import OptionalApiKeyPrincipal
from result_validator import validate_result
from supplier_profile_pipeline import (
    resolve_supplier_profile_fields,
)


router = APIRouter()
logger = logging.getLogger("document_processing.extraction")


def determine_processing_status(
    validation: dict,
    quality: dict,
    collection_validation: dict | None = None,
) -> str:
    if validation.get("valid") is not True:
        return "invalid"
    if (
        collection_validation is not None
        and collection_validation.get("valid") is not True
    ):
        return "invalid"
    if quality.get("requires_review") is True:
        return "review"
    return "accepted"


def get_extraction_document_config(
    document_type: str,
    config: dict,
) -> dict:
    document_config = config.get(document_type)
    if document_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Document type '{document_type}' "
                f"was not found"
            ),
        )
    if not is_document_type_ready(
        document_config
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Document type '{document_type}' "
                f"is not ready for extraction because "
                f"it has no configured fields"
            ),
        )
    return document_config


def elapsed_milliseconds(started_at: float) -> int:
    return max(
        0,
        round((perf_counter() - started_at) * 1000),
    )


def get_input_format(filename: str | None) -> str:
    suffix = Path(filename or "").suffix.lower()
    return suffix.removeprefix(".") or "unknown"


@router.post(
    "/extract-document",
    response_model=ExtractionResponseModel,
    response_model_exclude_none=True,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "description": "Document type was not found",
            "model": ApiErrorResponseModel,
        },
        status.HTTP_409_CONFLICT: {
            "description": (
                "Document type is not ready for extraction"
            ),
            "model": ApiErrorResponseModel,
        },
        status.HTTP_413_CONTENT_TOO_LARGE: {
            "description": "Uploaded file is too large",
            "model": DocumentInputErrorResponseModel,
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "description": "Unsupported file type",
            "model": DocumentInputErrorResponseModel,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": (
                "Request validation error or invalid "
                "document content"
            ),
            "model": (
                RequestValidationErrorResponseModel
                | DocumentInputErrorResponseModel
            ),
        },
    },
)
async def extract_document(
    processing_run_service: ProcessingRunServiceDependency,
    principal: OptionalApiKeyPrincipal,
    document_type: str = Form(
        ...,
        examples=["invoice"],
    ),
    file: UploadFile = File(...),
):
    config = load_config()
    document_config = (
        get_extraction_document_config(
            document_type=document_type,
            config=config,
        )
    )
    timer_started_at = perf_counter()
    step_timings = {}
    input_format = get_input_format(file.filename)
    processing_run = processing_run_service.start_run(
        document_type=document_type,
        filename=file.filename or "unknown",
        input_format=input_format,
        tenant_id=(
            principal.tenant_id
            if principal is not None
            else "default"
        ),
        created_by_type=(
            principal.principal_type
            if principal is not None
            else "system"
        ),
        created_by_subject=(
            principal.subject
            if principal is not None
            else "legacy"
        ),
    )
    set_processing_run_id(str(processing_run.id))
    logger.info(
        "Document processing started",
        extra={
            "event": "processing_run.started",
            "input_format": input_format,
        },
    )

    try:
        step_started_at = perf_counter()
        try:
            input_result = await extract_document_input(
                file
            )
        finally:
            step_timings["document_input_ms"] = (
                elapsed_milliseconds(step_started_at)
            )
        raw_text = input_result["text"]
        quality = input_result["quality"]
        selected_profile = None
        resolved_fields = None
        step_started_at = perf_counter()
        try:
            if "profiles" in document_config:
                profile_result = (
                    resolve_supplier_profile_fields(
                        document_config=document_config,
                        ocr_text=raw_text,
                    )
                )
                selected_profile = profile_result[
                    "profile"
                ]
                resolved_fields = profile_result[
                    "fields"
                ]
                if profile_result[
                    "requires_review"
                ]:
                    quality = {
                        **quality,
                        "status": "review",
                        "requires_review": True,
                        "warnings": [
                            *quality.get(
                                "warnings",
                                [],
                            ),
                            *profile_result[
                                "warnings"
                            ],
                        ],
                    }
        finally:
            step_timings["profile_resolution_ms"] = (
                elapsed_milliseconds(step_started_at)
            )
        step_started_at = perf_counter()
        try:
            llm_values = extract_values(raw_text)
        finally:
            step_timings["llm_extraction_ms"] = (
                elapsed_milliseconds(step_started_at)
            )
        step_started_at = perf_counter()
        try:
            engine_result = extract_document_data(
                document_type=document_type,
                config=config,
                raw_text=raw_text,
                llm_values=llm_values,
                profile_name=selected_profile,
                resolved_fields=resolved_fields,
            )
        finally:
            step_timings["document_engine_ms"] = (
                elapsed_milliseconds(step_started_at)
            )
        final_values = engine_result["fields"]
        collection_validation = engine_result.get(
            "collection_validation",
            {
                "valid": True,
                "errors": {},
            },
        )
        step_started_at = perf_counter()
        try:
            validation = validate_result(
                document_type=document_type,
                config=config,
                final_values=final_values,
                resolved_fields=resolved_fields,
            )
            processing_status = determine_processing_status(
                validation=validation,
                quality=quality,
                collection_validation=collection_validation,
            )
        finally:
            step_timings["validation_ms"] = (
                elapsed_milliseconds(step_started_at)
            )
        response = {
            "document_type": document_type,
            "processing_status": processing_status,
            "profile": selected_profile,
            "quality": quality,
            "raw_text": raw_text,
            "llm_values": llm_values,
            "final_values": final_values,
            "collections": engine_result["collections"],
            "collection_validation": collection_validation,
            "validation": validation,
        }
        processing_run_service.complete_run(
            processing_run.id,
            processing_status=processing_status,
            profile=selected_profile,
            requires_review=(
                quality.get("requires_review") is True
            ),
            duration_ms=elapsed_milliseconds(
                timer_started_at
            ),
            step_timings=step_timings,
            quality=quality,
            final_values=final_values,
            collections=engine_result["collections"],
            validation={
                "fields": validation,
                "collections": collection_validation,
            },
        )
        logger.info(
            "Document processing completed",
            extra={
                "event": "processing_run.completed",
                "processing_status": processing_status,
                "profile": selected_profile,
                "duration_ms": elapsed_milliseconds(
                    timer_started_at
                ),
            },
        )
        return response
    except PayloadTooLargeError as exc:
        processing_run_service.fail_run(
            processing_run.id,
            error={
                "type": type(exc).__name__,
                "detail": str(exc),
                "http_status": status.HTTP_413_CONTENT_TOO_LARGE,
            },
            duration_ms=elapsed_milliseconds(timer_started_at),
            step_timings=step_timings,
        )
        logger.warning(
            "Document processing rejected",
            extra={
                "event": "processing_run.failed",
                "error_type": type(exc).__name__,
                "http_status": status.HTTP_413_CONTENT_TOO_LARGE,
                "duration_ms": elapsed_milliseconds(timer_started_at),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except UnsupportedFileTypeError as exc:
        processing_run_service.fail_run(
            processing_run.id,
            error={
                "type": type(exc).__name__,
                "detail": str(exc),
                "http_status": (
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                ),
            },
            duration_ms=elapsed_milliseconds(
                timer_started_at
            ),
            step_timings=step_timings,
        )
        logger.warning(
            "Document processing rejected",
            extra={
                "event": "processing_run.failed",
                "error_type": type(exc).__name__,
                "http_status": (
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                ),
                "duration_ms": elapsed_milliseconds(
                    timer_started_at
                ),
            },
        )
        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=str(exc),
        ) from exc
    except InvalidDocumentInputError as exc:
        processing_run_service.fail_run(
            processing_run.id,
            error={
                "type": type(exc).__name__,
                "detail": str(exc),
                "http_status": (
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
            },
            duration_ms=elapsed_milliseconds(
                timer_started_at
            ),
            step_timings=step_timings,
        )
        logger.warning(
            "Document processing rejected",
            extra={
                "event": "processing_run.failed",
                "error_type": type(exc).__name__,
                "http_status": (
                    status.HTTP_422_UNPROCESSABLE_CONTENT
                ),
                "duration_ms": elapsed_milliseconds(
                    timer_started_at
                ),
            },
        )
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc
    except Exception as exc:
        processing_run_service.fail_run(
            processing_run.id,
            error={
                "type": type(exc).__name__,
                "detail": str(exc),
            },
            duration_ms=elapsed_milliseconds(
                timer_started_at
            ),
            step_timings=step_timings,
        )
        logger.exception(
            "Document processing failed",
            extra={
                "event": "processing_run.failed",
                "error_type": type(exc).__name__,
                "duration_ms": elapsed_milliseconds(
                    timer_started_at
                ),
            },
        )
        raise
