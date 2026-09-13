from typing import Any

from document_config_resolver import (
    DocumentConfigResolutionError,
    resolve_document_fields,
)


DOCUMENT_STATUS_DRAFT = "draft"
DOCUMENT_STATUS_READY = "ready"


def get_resolved_fields(
    document_config: Any,
) -> list[dict]:
    if not isinstance(document_config, dict):
        return []

    try:
        return resolve_document_fields(
            document_config
        )
    except DocumentConfigResolutionError:
        return []


def get_document_type_status(
    document_config: Any,
) -> str:
    fields = get_resolved_fields(
        document_config
    )

    if not fields:
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
    document_config: Any,
) -> dict:
    fields = get_resolved_fields(
        document_config
    )

    return {
        "status": get_document_type_status(
            document_config
        ),
        "ready": is_document_type_ready(
            document_config
        ),
        "field_count": len(fields),
    }