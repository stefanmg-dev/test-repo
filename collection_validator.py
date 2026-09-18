from typing import Any

from result_validator import validate_single_rule


class CollectionValidationError(ValueError):
    pass


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

    for collection_name, items in collections.items():
        schema = collection_schemas.get(collection_name)
        if schema is None:
            errors[f"_{collection_name}"] = [
                "Collection schema was not found"
            ]
            continue
        if not isinstance(schema, dict):
            raise CollectionValidationError(
                f"Collection '{collection_name}' schema "
                "must be an object"
            )
        if not isinstance(items, list):
            raise CollectionValidationError(
                f"Collection '{collection_name}' must be a list"
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
