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
from extraction_models import ExtractionResponseModel
from ocr_engine import (
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
) -> str:
    if validation.get("valid") is not True:
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
)
async def extract_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    config = load_config()

    document_config = (
        get_extraction_document_config(
            document_type=document_type,
            config=config,
        )
    )

    input_result = await extract_document_input(
        file
    )

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

    validation = validate_result(
        document_type=document_type,
        config=config,
        final_values=final_values,
        resolved_fields=resolved_fields,
    )

    processing_status = determine_processing_status(
        validation=validation,
        quality=quality,
    )

    return {
        "document_type": document_type,
        "processing_status": processing_status,
        "profile": selected_profile,
        "quality": quality,
        "raw_text": raw_text,
        "llm_values": llm_values,
        "final_values": final_values,
        "validation": validation,
    }
