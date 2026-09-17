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


def get_document_collections(
    document_config: dict,
):
    collections = document_config.get("collections", {})
    if not isinstance(collections, dict):
        raise DocumentConfigResolutionError(
            "'collections' must be an object"
        )
    return deepcopy(collections)


def get_profiles(
    document_config: dict,
):
    profiles = document_config.get(
        "profiles",
        {},
    )

    if not isinstance(profiles, dict):
        raise DocumentConfigResolutionError(
            "'profiles' must be an object"
        )

    return profiles


def get_default_profile(
    document_config: dict,
):
    default_profile = document_config.get(
        "default_profile"
    )

    if default_profile is None:
        return None

    if (
        not isinstance(default_profile, str)
        or not default_profile.strip()
    ):
        raise DocumentConfigResolutionError(
            "'default_profile' must be "
            "a non-empty string"
        )

    return default_profile.strip()


def get_profile_fields(
    document_config: dict,
    profile_name: str,
):
    profiles = get_profiles(
        document_config
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


def merge_field_layers(
    common_fields: list[dict],
    profile_fields: list[dict],
) -> list[dict]:
    profile_fields_by_name = {
        field["name"]: field
        for field in profile_fields
    }

    resolved_fields = []

    for common_field in common_fields:
        field_name = common_field["name"]

        resolved_fields.append(
            profile_fields_by_name.pop(
                field_name,
                common_field,
            )
        )

    resolved_fields.extend(
        profile_fields_by_name.values()
    )

    return resolved_fields


def resolve_profile_name(
    document_config: dict,
    profile_name: str | None,
    use_default_profile: bool = True,
):
    if profile_name is not None:
        if (
            not isinstance(profile_name, str)
            or not profile_name.strip()
        ):
            raise DocumentConfigResolutionError(
                "Profile name must be "
                "a non-empty string"
            )

        return profile_name.strip()

    if not isinstance(
        use_default_profile,
        bool,
    ):
        raise DocumentConfigResolutionError(
            "'use_default_profile' must "
            "be a boolean"
        )

    if not use_default_profile:
        return None

    return get_default_profile(
        document_config
    )


def resolve_document_fields(
    document_config: Any,
    profile_name: str | None = None,
    use_default_profile: bool = True,
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

        if "default_profile" in document_config:
            raise DocumentConfigResolutionError(
                "'default_profile' cannot be used "
                "with a legacy document "
                "configuration"
            )

        validate_unique_field_names(
            legacy_fields
        )

        return legacy_fields

    common_fields = get_common_fields(
        document_config
    )

    profiles = get_profiles(
        document_config
    )

    selected_profile = resolve_profile_name(
        document_config=document_config,
        profile_name=profile_name,
        use_default_profile=use_default_profile,
    )

    if (
        profiles
        and not selected_profile
        and use_default_profile
    ):
        raise DocumentConfigResolutionError(
            "A profile name is required"
        )

    validate_unique_field_names(
        common_fields
    )

    profile_fields: list[dict] = []

    if selected_profile:
        profile_fields = get_profile_fields(
            document_config=document_config,
            profile_name=selected_profile,
        )

        validate_unique_field_names(
            profile_fields
        )

    resolved_fields = merge_field_layers(
        common_fields=common_fields,
        profile_fields=profile_fields,
    )

    validate_unique_field_names(
        resolved_fields
    )

    return resolved_fields


def build_resolved_document_config(
    document_config: dict,
    profile_name: str | None = None,
) -> dict:
    resolved_config = {
        "fields": resolve_document_fields(
            document_config=document_config,
            profile_name=profile_name,
        )
    }
    if "collections" in document_config:
        resolved_config["collections"] = (
            get_document_collections(document_config)
        )
    return resolved_config
