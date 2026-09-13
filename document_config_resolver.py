from copy import deepcopy
from typing import Any


class DocumentConfigResolutionError(ValueError):
    pass


def get_legacy_fields(
    document_config: dict,
):
    fields = document_config.get("fields")

    if fields is None:
        return None

    if not isinstance(fields, list):
        raise DocumentConfigResolutionError(
            "'fields' must be a list"
        )

    return deepcopy(fields)


def get_common_fields(
    document_config: dict,
):
    common_fields = document_config.get(
        "common_fields",
        [],
    )

    if not isinstance(common_fields, list):
        raise DocumentConfigResolutionError(
            "'common_fields' must be a list"
        )

    return deepcopy(common_fields)


def get_profile_fields(
    document_config: dict,
    profile_name: str,
):
    profiles = document_config.get(
        "profiles",
        {},
    )

    if not isinstance(profiles, dict):
        raise DocumentConfigResolutionError(
            "'profiles' must be an object"
        )

    profile_config = profiles.get(
        profile_name
    )

    if profile_config is None:
        raise DocumentConfigResolutionError(
            f"Profile '{profile_name}' was not found"
        )

    if not isinstance(profile_config, dict):
        raise DocumentConfigResolutionError(
            f"Profile '{profile_name}' "
            "must be an object"
        )

    profile_fields = profile_config.get(
        "fields",
        [],
    )

    if not isinstance(profile_fields, list):
        raise DocumentConfigResolutionError(
            f"Profile '{profile_name}' fields "
            "must be a list"
        )

    return deepcopy(profile_fields)


def validate_unique_field_names(
    fields: list[dict],
) -> None:
    field_names: set[str] = set()

    for field in fields:
        if not isinstance(field, dict):
            raise DocumentConfigResolutionError(
                "Every field must be an object"
            )

        field_name = field.get("name")

        if (
            not isinstance(field_name, str)
            or not field_name.strip()
        ):
            raise DocumentConfigResolutionError(
                "Every field must have a name"
            )

        if field_name in field_names:
            raise DocumentConfigResolutionError(
                "Duplicate resolved field "
                f"'{field_name}'"
            )

        field_names.add(field_name)


def resolve_document_fields(
    document_config: Any,
    profile_name: str | None = None,
):
    if not isinstance(document_config, dict):
        raise DocumentConfigResolutionError(
            "Document configuration must "
            "be an object"
        )

    legacy_fields = get_legacy_fields(
        document_config
    )

    if legacy_fields is not None:
        if profile_name is not None:
            raise DocumentConfigResolutionError(
                "A profile cannot be selected for "
                "a legacy document configuration"
            )

        validate_unique_field_names(
            legacy_fields
        )

        return legacy_fields

    common_fields = get_common_fields(
        document_config
    )

    profiles = document_config.get(
        "profiles",
        {},
    )

    if not isinstance(profiles, dict):
        raise DocumentConfigResolutionError(
            "'profiles' must be an object"
        )

    if profiles and not profile_name:
        raise DocumentConfigResolutionError(
            "A profile name is required"
        )

    profile_fields: list[dict] = []

    if profile_name:
        profile_fields = get_profile_fields(
            document_config=document_config,
            profile_name=profile_name,
        )

    resolved_fields = (
        common_fields
        + profile_fields
    )

    validate_unique_field_names(
        resolved_fields
    )

    return resolved_fields


def build_resolved_document_config(
    document_config: dict,
    profile_name: str | None = None,
) -> dict:
    return {
        "fields": resolve_document_fields(
            document_config=document_config,
            profile_name=profile_name,
        )
    }