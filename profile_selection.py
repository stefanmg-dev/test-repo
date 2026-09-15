from typing import Any


UNKNOWN_SUPPLIER_WARNING = {
    "code": "unknown_supplier_profile",
    "message": (
        "No matching supplier profile was found"
    ),
}


class ProfileSelectionError(ValueError):
    pass


def get_profiles(
    document_config: dict,
) -> dict:
    profiles = document_config.get(
        "profiles",
        {},
    )

    if not isinstance(profiles, dict):
        raise ProfileSelectionError(
            "'profiles' must be an object"
        )

    return profiles


def validate_matched_profile_name(
    matched_profile_name: Any,
) -> str:
    if (
        not isinstance(
            matched_profile_name,
            str,
        )
        or not matched_profile_name.strip()
    ):
        raise ProfileSelectionError(
            "Matched profile name must be "
            "a non-empty string"
        )

    return matched_profile_name.strip()


def select_document_profile(
    document_config: dict,
    matched_profile_name: str | None,
) -> dict:
    if not isinstance(document_config, dict):
        raise ProfileSelectionError(
            "Document configuration must "
            "be an object"
        )

    profiles = get_profiles(
        document_config
    )

    if matched_profile_name is None:
        return {
            "profile": None,
            "use_default_profile": False,
            "requires_review": True,
            "warnings": [
                dict(UNKNOWN_SUPPLIER_WARNING)
            ],
        }

    profile_name = (
        validate_matched_profile_name(
            matched_profile_name
        )
    )

    if profile_name not in profiles:
        raise ProfileSelectionError(
            f"Profile '{profile_name}' "
            "was not found"
        )

    return {
        "profile": profile_name,
        "use_default_profile": False,
        "requires_review": False,
        "warnings": [],
    }
