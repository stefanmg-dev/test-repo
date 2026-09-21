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
from extraction_orchestrator import extract_document_data
from llm_engine import extract_values
from extraction_models import (
    DocumentInputErrorResponseModel,
    ExtractionResponseModel,
    RequestValidationErrorResponseModel,
)
from ocr_engine import (
    InvalidDocumentInputError,
    UnsupportedFileTypeError,
    extract_document_input,
    extract_text,
)
from result_validator import validate_result
from supplier_profile_pipeline import (
    resolve_supplier_profile_fields,
)


router = APIRouter()


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


@router.post(
    "/extract-document",
    response_model=ExtractionResponseModel,
    response_model_exclude_none=True,
    responses={
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

    try:
        input_result = await extract_document_input(
            file
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
            ),
            detail=str(exc),
        ) from exc
    except InvalidDocumentInputError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=str(exc),
        ) from exc

    raw_text = input_result["text"]
    quality = input_result["quality"]

    selected_profile = None
    resolved_fields = None

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

    llm_values = extract_values(raw_text)

    engine_result = extract_document_data(
        document_type=document_type,
        config=config,
        raw_text=raw_text,
        llm_values=llm_values,
        profile_name=selected_profile,
        resolved_fields=resolved_fields,
    )
    final_values = engine_result["fields"]
    collection_validation = engine_result.get(
        "collection_validation",
        {
            "valid": True,
            "errors": {},
        },
    )

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

    return {
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
