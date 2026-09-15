import re
from typing import Any


SUPPORTED_FIELD_TYPES = {
    "constant",
    "regex",
    "regex_list",
    "nearby",
    "llm",
}

SUPPORTED_OCCURRENCES = {"first", "last"}
SUPPORTED_DIRECTIONS = {"before", "after", "both"}
PROFILE_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class ConfigValidationError(ValueError):
    pass


def require_non_empty_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigValidationError(
            f"{path} must be a non-empty string"
        )

    return value.strip()


def validate_regex(pattern: Any, path: str) -> None:
    pattern = require_non_empty_string(pattern, path)

    try:
        re.compile(pattern)
    except re.error as exc:
        raise ConfigValidationError(
            f"{path} contains invalid regex: {exc}"
        ) from exc


def validate_occurrence(field: dict, path: str) -> None:
    occurrence = field.get("occurrence", "last")

    if occurrence not in SUPPORTED_OCCURRENCES:
        raise ConfigValidationError(
            f"{path}.occurrence must be one of: "
            f"{sorted(SUPPORTED_OCCURRENCES)}"
        )


def validate_constant_field(field: dict, path: str) -> None:
    if "value" not in field:
        raise ConfigValidationError(
            f"{path}.value is required for constant fields"
        )


def validate_regex_field(field: dict, path: str) -> None:
    validate_regex(field.get("rule"), f"{path}.rule")
    validate_occurrence(field, path)


def validate_regex_list_field(field: dict, path: str) -> None:
    rules = field.get("rules")

    if not isinstance(rules, list) or not rules:
        raise ConfigValidationError(
            f"{path}.rules must be a non-empty list"
        )

    for rule_index, rule in enumerate(rules):
        validate_regex(rule, f"{path}.rules[{rule_index}]")

    validate_occurrence(field, path)


def validate_nearby_field(field: dict, path: str) -> None:
    require_non_empty_string(field.get("anchor"), f"{path}.anchor")
    validate_regex(field.get("pattern"), f"{path}.pattern")

    direction = field.get("direction", "both")

    if direction not in SUPPORTED_DIRECTIONS:
        raise ConfigValidationError(
            f"{path}.direction must be one of: "
            f"{sorted(SUPPORTED_DIRECTIONS)}"
        )

    validate_occurrence(field, path)

    window_size = field.get("window_size", 400)

    if (
        not isinstance(window_size, int)
        or isinstance(window_size, bool)
        or window_size <= 0
    ):
        raise ConfigValidationError(
            f"{path}.window_size must be a positive integer"
        )


def validate_field(field: Any, path: str) -> str:
    if not isinstance(field, dict):
        raise ConfigValidationError(f"{path} must be an object")

    field_name = require_non_empty_string(
        field.get("name"),
        f"{path}.name",
    )
    field_type = require_non_empty_string(
        field.get("type"),
        f"{path}.type",
    )

    if field_type not in SUPPORTED_FIELD_TYPES:
        raise ConfigValidationError(
            f"{path}.type '{field_type}' is not supported. "
            f"Supported types: {sorted(SUPPORTED_FIELD_TYPES)}"
        )

    if field_type == "constant":
        validate_constant_field(field, path)
    elif field_type == "regex":
        validate_regex_field(field, path)
    elif field_type == "regex_list":
        validate_regex_list_field(field, path)
    elif field_type == "nearby":
        validate_nearby_field(field, path)

    return field_name


def validate_field_list(
    fields: Any,
    path: str,
    existing_names: set[str] | None = None,
) -> set[str]:
    if not isinstance(fields, list):
        raise ConfigValidationError(f"{path} must be a list")

    field_names = set(existing_names or set())

    for field_index, field in enumerate(fields):
        field_path = f"{path}[{field_index}]"
        field_name = validate_field(field, field_path)

        if field_name in field_names:
            raise ConfigValidationError(
                f"{field_path}.name contains duplicate "
                f"field name '{field_name}'"
            )

        field_names.add(field_name)

    return field_names


def validate_profile_name(profile_name: Any, path: str) -> str:
    profile_name = require_non_empty_string(profile_name, path)

    if not PROFILE_NAME_PATTERN.fullmatch(profile_name):
        raise ConfigValidationError(
            f"{path} must match ^[a-z][a-z0-9_]*$"
        )

    return profile_name


def validate_legacy_document_type(
    document_config: dict,
    path: str,
) -> None:
    validate_field_list(
        document_config.get("fields"),
        f"{path}.fields",
    )


def validate_profile_document_type(
    document_config: dict,
    path: str,
) -> None:
    common_names = validate_field_list(
        document_config.get("common_fields", []),
        f"{path}.common_fields",
    )

    profiles = document_config.get("profiles", {})

    if not isinstance(profiles, dict):
        raise ConfigValidationError(
            f"{path}.profiles must be an object"
        )

    default_profile = document_config.get("default_profile")

    if default_profile is not None:
        default_profile = validate_profile_name(
            default_profile,
            f"{path}.default_profile",
        )

        if default_profile not in profiles:
            raise ConfigValidationError(
                f"{path}.default_profile '{default_profile}' "
                "was not found in profiles"
            )

    for profile_name, profile_config in profiles.items():
        profile_path = f"{path}.profiles.{profile_name}"
        validate_profile_name(profile_name, f"{profile_path}.name")

        if not isinstance(profile_config, dict):
            raise ConfigValidationError(
                f"{profile_path} must be an object"
            )

        unknown_keys = set(profile_config) - {"fields"}
        if unknown_keys:
            raise ConfigValidationError(
                f"{profile_path} contains unsupported properties: "
                f"{sorted(unknown_keys)}"
            )

        validate_field_list(
            profile_config.get("fields", []),
            f"{profile_path}.fields",
        )


def validate_document_type(
    document_type: str,
    document_config: Any,
) -> None:
    path = f"document_types.{document_type}"

    if not isinstance(document_config, dict):
        raise ConfigValidationError(f"{path} must be an object")

    allowed_keys = {"fields", "default_profile", "common_fields", "profiles"}
    unknown_keys = set(document_config) - allowed_keys

    if unknown_keys:
        raise ConfigValidationError(
            f"{path} contains unsupported properties: "
            f"{sorted(unknown_keys)}"
        )

    uses_legacy = "fields" in document_config
    uses_profiles = (
        "default_profile" in document_config
        or "common_fields" in document_config
        or "profiles" in document_config
    )

    if uses_legacy and uses_profiles:
        raise ConfigValidationError(
            f"{path} cannot combine legacy 'fields' with "
            "'default_profile', 'common_fields' or 'profiles'"
        )

    if not uses_legacy and not uses_profiles:
        raise ConfigValidationError(
            f"{path} must define either 'fields' or "
            "profile-based configuration"
        )

    if uses_legacy:
        validate_legacy_document_type(document_config, path)
    else:
        validate_profile_document_type(document_config, path)


def validate_config(config: Any) -> None:
    if not isinstance(config, dict):
        raise ConfigValidationError(
            "Configuration root must be an object"
        )

    if not config:
        raise ConfigValidationError(
            "Configuration cannot be empty"
        )

    for document_type, document_config in config.items():
        require_non_empty_string(
            document_type,
            "document type name",
        )
        validate_document_type(
            document_type,
            document_config,
        )
