from fastapi import HTTPException, status

from config_store import save_config
from config_validator import ConfigValidationError


def save_validated_config(config: dict) -> None:
    try:
        save_config(config)
    except ConfigValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


def get_document_type_or_404(
    config: dict,
    document_type: str,
) -> dict:
    document_config = config.get(document_type)
    if document_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Document type '{document_type}' "
                "was not found"
            ),
        )
    return document_config


def find_field_index(
    fields: list[dict],
    field_name: str,
) -> int | None:
    for index, field in enumerate(fields):
        if field.get("name") == field_name:
            return index
    return None


def get_profile_or_404(
    document_config: dict,
    profile_name: str,
) -> dict:
    profiles = document_config.get("profiles")
    if not isinstance(profiles, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Document type does not use profile "
                "configuration"
            ),
        )
    profile_config = profiles.get(profile_name)
    if profile_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{profile_name}' was not found",
        )
    return profile_config


def ensure_profile_based_config(
    document_config: dict,
) -> None:
    if "fields" in document_config:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Document type uses legacy fields "
                "configuration"
            ),
        )
