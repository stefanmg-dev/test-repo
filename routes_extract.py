from fastapi import APIRouter, File, Form, UploadFile

from config_store import load_config
from extraction_orchestrator import apply_rules
from llm_engine import extract_values
from ocr_engine import extract_text
from result_validator import validate_result


router = APIRouter()


@router.post("/extract-document")
async def extract_document(
    document_type: str = Form(...),
    file: UploadFile = File(...)
):
    config = load_config()

    raw_text = await extract_text(file)

    llm_values = extract_values(raw_text)

    final_values = apply_rules(
        document_type=document_type,
        config=config,
        raw_text=raw_text,
        llm_values=llm_values
    )

    validation = validate_result(
        document_type=document_type,
        config=config,
        final_values=final_values
    )

    return {
        "document_type": document_type,
        "raw_text": raw_text,
        "llm_values": llm_values,
        "final_values": final_values,
        "validation": validation
    }