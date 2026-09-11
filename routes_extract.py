from fastapi import APIRouter, UploadFile, File, Form
from ocr_engine import extract_text
from llm_engine import extract_values
from extraction_orchestrator import apply_rules
from config_store import load_config

router = APIRouter()

@router.post("/extract-document")
async def extract_document(
    document_type: str = Form(...),
    file: UploadFile = File(...)
):

    cfg = load_config()

    raw_text = await extract_text(file)
    llm_values = extract_values(raw_text)

    final_values = apply_rules(
        document_type=document_type,
        config=cfg,
        raw_text=raw_text,
        llm_values=llm_values
    )

    return {
        "document_type": document_type,
        "raw_text": raw_text,
        "llm_values": llm_values,
        "final_values": final_values
    }
