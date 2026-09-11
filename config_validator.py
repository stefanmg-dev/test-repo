import re
from typing import Any


SUPPORTED_FIELD_TYPES = {
    "constant",
    "regex",
    "regex_list",
    "nearby",
    "llm",
}

SUPPORTED_OCCURRENCES = {
    "first",
    "last",
}

SUPPORTED_DIRECTIONS = {
    "before",
    "after",
    "both",
}


class ConfigValidationError(ValueError):
    pass


def require_non_empty_string(
    value: Any,
    path: str
) -> str:
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
    validate_regex(
        field.get("rule"),
        f"{path}.rule"
    )

    validate_occurrence(field, path)


def validate_regex_list_field(field: dict, path: str) -> None:
    rules = field.get("rules")

    if not isinstance(rules, list) or not rules:
        raise ConfigValidationError(
            f"{path}.rules must be a non-empty list"
        )

    for rule_index, rule in enumerate(rules):
        validate_regex(
            rule,
            f"{path}.rules[{rule_index}]"
        )

    validate_occurrence(field, path)


def validate_nearby_field(field: dict, path: str) -> None:
    require_non_empty_string(
        field.get("anchor"),
        f"{path}.anchor"
    )

    validate_regex(
        field.get("pattern"),
        f"{path}.pattern"
    )

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


def validate_field(
    field: Any,
    path: str
) -> str:
    if not isinstance(field, dict):
        raise ConfigValidationError(
            f"{path} must be an object"
        )

    field_name = require_non_empty_string(
        field.get("name"),
        f"{path}.name"
    )

    field_type = require_non_empty_string(
        field.get("type"),
        f"{path}.type"
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


def validate_document_type(
    document_type: str,
    document_config: Any
) -> None:
    path = f"document_types.{document_type}"

    if not isinstance(document_config, dict):
        raise ConfigValidationError(
            f"{path} must be an object"
        )

    fields = document_config.get("fields")

    if not isinstance(fields, list) or not fields:
        raise ConfigValidationError(
            f"{path}.fields must be a non-empty list"
        )

    field_names = set()

    for field_index, field in enumerate(fields):
        field_path = f"{path}.fields[{field_index}]"

        field_name = validate_field(
            field,
            field_path
        )

        if field_name in field_names:
            raise ConfigValidationError(
                f"{field_path}.name contains duplicate "
                f"field name '{field_name}'"
            )

        field_names.add(field_name)


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
            "document type name"
        )

        validate_document_type(
            document_type,
            document_config
        )