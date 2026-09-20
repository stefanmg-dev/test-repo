from decimal import Decimal, InvalidOperation


class CollectionSummaryValidationError(ValueError):
    pass


SUPPORTED_SUMMARY_VALIDATION_TYPES = {
    "collection_sum_equals_field",
}


def parse_decimal(value):
    if value is None or isinstance(value, bool):
        return None

    normalized = (
        str(value)
        .strip()
        .replace(" ", "")
        .replace(",", ".")
    )

    if not normalized:
        return None

    try:
        return Decimal(normalized)
    except InvalidOperation:
        return None


def validate_collection_sum_equals_field(
    fields,
    collections,
    validation,
):
    collection_name = validation.get("collection")
    item_field = validation.get("item_field")
    target_field = validation.get("target_field")

    for property_name, value in (
        ("collection", collection_name),
        ("item_field", item_field),
        ("target_field", target_field),
    ):
        if not isinstance(value, str) or not value:
            raise CollectionSummaryValidationError(
                "collection_sum_equals_field must define "
                f"a non-empty '{property_name}'"
            )

    items = collections.get(collection_name)

    if not isinstance(items, list):
        return None

    target_value = parse_decimal(
        fields.get(target_field)
    )

    if target_value is None:
        return None

    item_values = []

    for item in items:
        if not isinstance(item, dict):
            return None

        item_value = parse_decimal(
            item.get(item_field)
        )

        if item_value is None:
            return None

        item_values.append(item_value)

    if sum(item_values, Decimal("0")) != target_value:
        return validation.get(
            "message",
            (
                f"Sum of {collection_name}.{item_field} "
                f"must equal {target_field}"
            ),
        )

    return None


def validate_collection_summaries(
    fields,
    collections,
    validations,
):
    if not isinstance(fields, dict):
        raise CollectionSummaryValidationError(
            "Fields must be an object"
        )

    if not isinstance(collections, dict):
        raise CollectionSummaryValidationError(
            "Collections must be an object"
        )

    if not isinstance(validations, list):
        raise CollectionSummaryValidationError(
            "Summary validations must be a list"
        )

    errors = {}

    for validation in validations:
        if not isinstance(validation, dict):
            raise CollectionSummaryValidationError(
                "Summary validation must be an object"
            )

        validation_type = validation.get("type")

        if (
            validation_type
            not in SUPPORTED_SUMMARY_VALIDATION_TYPES
        ):
            raise CollectionSummaryValidationError(
                "Unsupported summary validation type: "
                f"{validation_type}"
            )

        if (
            validation_type
            == "collection_sum_equals_field"
        ):
            error = (
                validate_collection_sum_equals_field(
                    fields=fields,
                    collections=collections,
                    validation=validation,
                )
            )

            if error:
                target_field = validation.get(
                    "target_field"
                )
                errors[
                    f"_summary.{target_field}"
                ] = [error]

    return {
        "valid": not bool(errors),
        "errors": errors,
    }
