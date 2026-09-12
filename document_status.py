from typing import Any


DOCUMENT_STATUS_DRAFT = "draft"
DOCUMENT_STATUS_READY = "ready"


def get_document_type_status(
    document_config: Any
) -> str:
    if not isinstance(document_config, dict):
        return DOCUMENT_STATUS_DRAFT

    fields = document_config.get("fields")

    if not isinstance(fields, list) or not fields:
        return DOCUMENT_STATUS_DRAFT

    return DOCUMENT_STATUS_READY


def is_document_type_ready(
    document_config: Any
) -> bool:
    return (
        get_document_type_status(document_config)
        == DOCUMENT_STATUS_READY
    )


def build_document_type_metadata(
    document_config: Any
) -> dict:
    if not isinstance(document_config, dict):
        fields = []
    else:
        fields = document_config.get("fields", [])

        if not isinstance(fields, list):
            fields = []

    return {
        "status": get_document_type_status(
            document_config
        ),
        "ready": is_document_type_ready(
            document_config
        ),
        "field_count": len(fields),
    }