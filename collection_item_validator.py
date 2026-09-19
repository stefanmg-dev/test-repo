from decimal import Decimal, InvalidOperation


class CollectionItemValidationError(ValueError):
    pass


SUPPORTED_ITEM_VALIDATION_TYPES = {
    "difference_equals",
}


def parse_decimal(value):
    if value is None or isinstance(value, bool):
        return None

    normalized = str(value).strip()

    if not normalized:
        return None

    normalized = (
        normalized
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def validate_difference_equals(item, validation):
    minuend_field = validation.get("minuend")
    subtrahend_field = validation.get("subtrahend")
    result_field = validation.get("result")

    for property_name, field_name in (
        ("minuend", minuend_field),
        ("subtrahend", subtrahend_field),
        ("result", result_field),
    ):
        if (
            not isinstance(field_name, str)
            or not field_name
        ):
            raise CollectionItemValidationError(
                "difference_equals validation must define "
                f"a non-empty '{property_name}' field"
            )

    minuend = parse_decimal(
        item.get(minuend_field)
    )
    subtrahend = parse_decimal(
        item.get(subtrahend_field)
    )
    result = parse_decimal(
        item.get(result_field)
    )

    if (
        minuend is None
        or subtrahend is None
        or result is None
    ):
        return None

    if minuend - subtrahend != result:
        return validation.get(
            "message",
            (
                f"{result_field} must equal "
                f"{minuend_field} minus "
                f"{subtrahend_field}"
            ),
        )

    return None


def validate_collection_item(item, validations):
    if not isinstance(validations, list):
        raise CollectionItemValidationError(
            "Item validations must be a list"
        )

    errors = []

    for validation in validations:
        if not isinstance(validation, dict):
            raise CollectionItemValidationError(
                "Item validation must be an object"
            )

        validation_type = validation.get("type")

        if (
            validation_type
            not in SUPPORTED_ITEM_VALIDATION_TYPES
        ):
            raise CollectionItemValidationError(
                "Unsupported collection item validation "
                f"type: {validation_type}"
            )

        if validation_type == "difference_equals":
            error = validate_difference_equals(
                item=item,
                validation=validation,
            )

            if error:
                errors.append(error)

    return errors
