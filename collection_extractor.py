from typing import Any

from extraction_orchestrator import (
    extract_regex_value,
    normalize_field_value,
)


class CollectionExtractionError(ValueError):
    pass


def extract_collection_item(
    item_text: str,
    fields: list[dict],
) -> dict:
    if not isinstance(item_text, str):
        raise CollectionExtractionError(
            "Collection item text must be a string"
        )
    if not isinstance(fields, list):
        raise CollectionExtractionError(
            "Collection fields must be a list"
        )

    item = {}

    for field in fields:
        if not isinstance(field, dict):
            raise CollectionExtractionError(
                "Every collection field must be an object"
            )

        field_name = field.get("name")
        field_type = field.get("type")

        if not isinstance(field_name, str) or not field_name:
            raise CollectionExtractionError(
                "Every collection field must have a name"
            )

        value: Any = None

        if field_type == "constant":
            value = field.get("value")
        elif field_type == "regex":
            value = extract_regex_value(
                text=item_text,
                pattern=field.get("rule", ""),
                occurrence=field.get(
                    "occurrence",
                    "last",
                ),
            )
        elif field_type == "regex_list":
            for pattern in field.get("rules", []):
                value = extract_regex_value(
                    text=item_text,
                    pattern=pattern,
                    occurrence=field.get(
                        "occurrence",
                        "last",
                    ),
                )
                if value is not None:
                    break
        else:
            raise CollectionExtractionError(
                "Unsupported collection field type: "
                f"{field_type!r}"
            )

        item[field_name] = normalize_field_value(
            field=field,
            value=value,
        )

    return item


def extract_collection_items(
    item_texts: list[str],
    fields: list[dict],
) -> list[dict]:
    if not isinstance(item_texts, list):
        raise CollectionExtractionError(
            "Collection item texts must be a list"
        )

    return [
        extract_collection_item(
            item_text=item_text,
            fields=fields,
        )
        for item_text in item_texts
    ]
