from fastapi import APIRouter, Form
from config_store import load_config, save_config

router = APIRouter()

@router.get("/get-document-types")
def get_document_types():
    return load_config()

@router.post("/add-field")
def add_field(
    document_type: str = Form(...),
    field_name: str = Form(...),
    label_bg: str = Form(...),
    label_en: str = Form(...),
    type: str = Form(...),
    rule: str = Form("")
):
    cfg = load_config()

    if document_type not in cfg:
        return {"error": "Unknown document type"}

    cfg[document_type]["fields"].append({
        "name": field_name,
        "label": {"bg": label_bg, "en": label_en},
        "type": type,
        "rule": rule
    })

    save_config(cfg)
    return {"status": "ok"}


@router.post("/update-field")
def update_field(
    document_type: str = Form(...),
    field_name: str = Form(...),
    label_bg: str = Form(...),
    label_en: str = Form(...),
    type: str = Form(...),
    rule: str = Form("")
):
    cfg = load_config()

    fields = cfg[document_type]["fields"]
    for field in fields:
        if field["name"] == field_name:
            field["label"]["bg"] = label_bg
            field["label"]["en"] = label_en
            field["type"] = type
            field["rule"] = rule
            break

    save_config(cfg)
    return {"status": "ok"}


@router.delete("/delete-field")
def delete_field(document_type: str, field_name: str):
    cfg = load_config()

    cfg[document_type]["fields"] = [
        f for f in cfg[document_type]["fields"] if f["name"] != field_name
    ]

    save_config(cfg)
    return {"status": "ok"}
