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
from extraction_orchestrator import apply_rules
from llm_engine import extract_values
from ocr_engine import (
    extract_document_input,
    extract_text,
)
from result_validator import validate_result


router = APIRouter()


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


@router.post("/extract-document")
async def extract_document(
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    config = load_config()

    get_extraction_document_config(
        document_type=document_type,
        config=config,
    )

    input_result = await extract_document_input(
        file
    )

    raw_text = input_result["text"]
    quality = input_result["quality"]

    llm_values = extract_values(raw_text)

    final_values = apply_rules(
        document_type=document_type,
        config=config,
        raw_text=raw_text,
        llm_values=llm_values,
    )

    validation = validate_result(
        document_type=document_type,
        config=config,
        final_values=final_values,
    )

    return {
        "document_type": document_type,
        "quality": quality,
        "raw_text": raw_text,
        "llm_values": llm_values,
        "final_values": final_values,
        "validation": validation,
    }