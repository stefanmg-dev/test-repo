import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from document_config_resolver import resolve_document_fields


SUPPORTED_VALIDATION_TYPES = {
    "required",
    "regex",
    "date",
    "decimal",
}


def validate_required(
    value: Any,
    validation: dict
) -> str | None:
    if value is None:
        return validation.get(
            "message",
            "Value is required"
        )

    if isinstance(value, str) and not value.strip():
        return validation.get(
            "message",
            "Value is required"
        )

    return None


def validate_regex(
    value: Any,
    validation: dict
) -> str | None:
    if value is None:
        return None

    pattern = validation.get("pattern")

    if not pattern:
        return "Validation regex pattern is missing"

    if not re.fullmatch(pattern, str(value)):
        return validation.get(
            "message",
            "Value has invalid format"
        )

    return None


def validate_date(
    value: Any,
    validation: dict
) -> str | None:
    if value is None:
        return None

    date_format = validation.get(
        "format",
        "%d.%m.%Y"
    )

    try:
        datetime.strptime(
            str(value),
            date_format
        )

    except ValueError:
        return validation.get(
            "message",
            "Value is not a valid date"
        )

    return None


def validate_decimal(
    value: Any,
    validation: dict
) -> str | None:
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))

    except InvalidOperation:
        return validation.get(
            "message",
            "Value is not a valid decimal number"
        )

    minimum = validation.get("minimum")
    maximum = validation.get("maximum")

    if minimum is not None:
        try:
            minimum_value = Decimal(str(minimum))
        except InvalidOperation:
            return "Decimal minimum configuration is invalid"

        if decimal_value < minimum_value:
            return validation.get(
                "message",
                f"Value must be at least {minimum}"
            )

    if maximum is not None:
        try:
            maximum_value = Decimal(str(maximum))
        except InvalidOperation:
            return "Decimal maximum configuration is invalid"

        if decimal_value > maximum_value:
            return validation.get(
                "message",
                f"Value must not exceed {maximum}"
            )

    return None


def validate_single_rule(
    value: Any,
    validation: dict
) -> str | None:
    validation_type = validation.get("type")

    if validation_type == "required":
        return validate_required(
            value,
            validation
        )

    if validation_type == "regex":
        return validate_regex(
            value,
            validation
        )

    if validation_type == "date":
        return validate_date(
            value,
            validation
        )

    if validation_type == "decimal":
        return validate_decimal(
            value,
            validation
        )

    return (
        f"Unsupported validation type: "
        f"{validation_type}"
    )


def validate_result(
    document_type: str,
    config: dict,
    final_values: dict
) -> dict:
    document_config = config.get(document_type)

    if not document_config:
        return {
            "valid": False,
            "errors": {
                "_document_type": [
                    f"Unknown document type: {document_type}"
                ]
            }
        }

    fields = resolve_document_fields(
        document_config
    )

    errors = {}

    for field in fields:
        field_name = field.get("name")

        if not field_name:
            continue

        value = final_values.get(field_name)
        validation_rules = field.get(
            "validation",
            []
        )

        field_errors = []

        for validation in validation_rules:
            error = validate_single_rule(
                value,
                validation
            )

            if error:
                field_errors.append(error)

        if field_errors:
            errors[field_name] = field_errors

    return {
        "valid": not bool(errors),
        "errors": errors
    }