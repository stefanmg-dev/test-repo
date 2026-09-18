from typing import Any

from result_validator import validate_single_rule


class CollectionValidationError(ValueError):
    pass


SUPPORTED_CARDINALITIES = {
    "zero_or_more",
    "one_or_more",
    "exactly_one",
}


def validate_collection_cardinality(
    collection_name: str,
    items: list,
    schema: dict,
) -> list[str]:
    cardinality = schema.get(
        "cardinality",
        "zero_or_more",
    )

    if cardinality not in SUPPORTED_CARDINALITIES:
        raise CollectionValidationError(
            f"Collection '{collection_name}' has "
            f"unsupported cardinality: {cardinality}"
        )

    if cardinality == "one_or_more" and not items:
        return [
            "Collection must contain at least one item"
        ]

    if cardinality == "exactly_one" and len(items) != 1:
        return [
            "Collection must contain exactly one item"
        ]

    return []


def validate_collections(
    collections: dict[str, list[dict[str, Any]]],
    collection_schemas: dict,
) -> dict:
    if not isinstance(collections, dict):
        raise CollectionValidationError(
            "Collections must be an object"
        )
    if not isinstance(collection_schemas, dict):
        raise CollectionValidationError(
            "Collection schemas must be an object"
        )

    errors: dict[str, list[str]] = {}

    for collection_name in collections:
        if collection_name not in collection_schemas:
            errors[f"_{collection_name}"] = [
                "Collection schema was not found"
            ]

    for collection_name, schema in collection_schemas.items():
        if not isinstance(schema, dict):
            raise CollectionValidationError(
                f"Collection '{collection_name}' schema "
                "must be an object"
            )

        items = collections.get(collection_name, [])

        if not isinstance(items, list):
            raise CollectionValidationError(
                f"Collection '{collection_name}' must be a list"
            )

        cardinality_errors = (
            validate_collection_cardinality(
                collection_name=collection_name,
                items=items,
                schema=schema,
            )
        )
        if cardinality_errors:
            errors[f"_{collection_name}"] = (
                cardinality_errors
            )

        fields = schema.get("fields", [])
        if not isinstance(fields, list):
            raise CollectionValidationError(
                f"Collection '{collection_name}' fields "
                "must be a list"
            )

        for index, item in enumerate(items):
            if not isinstance(item, dict):
                errors[f"{collection_name}[{index}]"] = [
                    "Collection item must be an object"
                ]
                continue

            for field in fields:
                if not isinstance(field, dict):
                    raise CollectionValidationError(
                        f"Collection '{collection_name}' field "
                        "must be an object"
                    )
                field_name = field.get("name")
                if not isinstance(field_name, str) or not field_name:
                    raise CollectionValidationError(
                        f"Collection '{collection_name}' field "
                        "must have a name"
                    )

                field_errors = []
                value = item.get(field_name)
                for validation in field.get("validation", []):
                    error = validate_single_rule(
                        value=value,
                        validation=validation,
                    )
                    if error:
                        field_errors.append(error)

                if field_errors:
                    path = (
                        f"{collection_name}[{index}]."
                        f"{field_name}"
                    )
                    errors[path] = field_errors

    return {
        "valid": not bool(errors),
        "errors": errors,
    }
