from typing import Any

from extraction_orchestrator import (
    extract_regex_value,
    normalize_field_value,
)


class CollectionExtractionError(ValueError):
    pass


def extract_collection_item_with_evidence(
    item_text: str,
    fields: list[dict],
) -> tuple[dict, dict]:
    if not isinstance(item_text, str):
        raise CollectionExtractionError(
            "Collection item text must be a string"
        )
    if not isinstance(fields, list):
        raise CollectionExtractionError(
            "Collection fields must be a list"
        )

    item = {}
    item_evidence = {}

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

        evidence = {
            "method": field_type or "unknown",
            "matched": False,
            "normalized": False,
        }
        value: Any = None

        if field_type == "constant":
            value = field.get("value")
            evidence["matched"] = value is not None
            if value is None:
                evidence["failure_reason"] = "constant_value_missing"

        elif field_type == "regex":
            occurrence = field.get("occurrence", "last")
            value = extract_regex_value(
                text=item_text,
                pattern=field.get("rule", ""),
                occurrence=occurrence,
            )
            evidence["occurrence"] = occurrence
            evidence["matched"] = value is not None
            if value is None:
                evidence["failure_reason"] = "pattern_not_matched"

        elif field_type == "regex_list":
            occurrence = field.get("occurrence", "last")
            evidence["occurrence"] = occurrence
            for rule_index, pattern in enumerate(field.get("rules", [])):
                candidate = extract_regex_value(
                    text=item_text,
                    pattern=pattern,
                    occurrence=occurrence,
                )
                if candidate is not None:
                    value = candidate
                    evidence["matched"] = True
                    evidence["rule_index"] = rule_index
                    break
            if value is None:
                evidence["failure_reason"] = "no_pattern_matched"

        else:
            raise CollectionExtractionError(
                "Unsupported collection field type: "
                f"{field_type!r}"
            )

        normalized_value = normalize_field_value(
            field=field,
            value=value,
        )
        evidence["normalized"] = normalized_value != value
        item[field_name] = normalized_value
        item_evidence[field_name] = evidence

    return item, item_evidence


def extract_collection_item(
    item_text: str,
    fields: list[dict],
) -> dict:
    item, _ = extract_collection_item_with_evidence(
        item_text=item_text,
        fields=fields,
    )
    return item


def extract_collection_items_with_evidence(
    item_texts: list[str],
    fields: list[dict],
) -> tuple[list[dict], list[dict]]:
    if not isinstance(item_texts, list):
        raise CollectionExtractionError(
            "Collection item texts must be a list"
        )

    items = []
    items_evidence = []
    for item_text in item_texts:
        item, item_evidence = extract_collection_item_with_evidence(
            item_text=item_text,
            fields=fields,
        )
        items.append(item)
        items_evidence.append(item_evidence)
    return items, items_evidence


def extract_collection_items(
    item_texts: list[str],
    fields: list[dict],
) -> list[dict]:
    items, _ = extract_collection_items_with_evidence(
        item_texts=item_texts,
        fields=fields,
    )
    return items
