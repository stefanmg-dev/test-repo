from collection_extractor import (
    extract_collection_items,
    extract_collection_items_with_evidence,
)
from collection_splitter import split_collection_blocks


class CollectionPipelineError(ValueError):
    pass


def extract_collection_from_text(
    raw_text: str,
    start_pattern: str,
    fields: list[dict],
) -> list[dict]:
    item_blocks = split_collection_blocks(
        raw_text=raw_text,
        start_pattern=start_pattern,
    )
    return extract_collection_items(
        item_texts=item_blocks,
        fields=fields,
    )


def extract_collection_from_schema(
    raw_text: str,
    collection_schema: dict,
) -> list[dict]:
    if not isinstance(collection_schema, dict):
        raise CollectionPipelineError(
            "Collection schema must be an object"
        )

    start_pattern = collection_schema.get("start_pattern")
    fields = collection_schema.get("fields")

    if not isinstance(start_pattern, str) or not start_pattern:
        raise CollectionPipelineError(
            "Collection schema start_pattern must be "
            "a non-empty string"
        )
    if not isinstance(fields, list):
        raise CollectionPipelineError(
            "Collection schema fields must be a list"
        )

    return extract_collection_from_text(
        raw_text=raw_text,
        start_pattern=start_pattern,
        fields=fields,
    )


def extract_collection_from_schema_with_evidence(
    raw_text: str,
    collection_schema: dict,
) -> tuple[list[dict], list[dict]]:
    if not isinstance(collection_schema, dict):
        raise CollectionPipelineError(
            "Collection schema must be an object"
        )

    start_pattern = collection_schema.get("start_pattern")
    fields = collection_schema.get("fields")
    if not isinstance(start_pattern, str) or not start_pattern:
        raise CollectionPipelineError(
            "Collection schema start_pattern must be "
            "a non-empty string"
        )
    if not isinstance(fields, list):
        raise CollectionPipelineError(
            "Collection schema fields must be a list"
        )

    item_blocks = split_collection_blocks(
        raw_text=raw_text,
        start_pattern=start_pattern,
    )
    return extract_collection_items_with_evidence(
        item_texts=item_blocks,
        fields=fields,
    )


def build_collection_item_evidence(
    item: dict,
    fields: list[dict],
) -> dict:
    evidence = {}
    for field in fields:
        field_name = field.get("name")
        if not isinstance(field_name, str) or not field_name:
            continue

        value = item.get(field_name)
        field_type = field.get("type")
        field_evidence = {
            "method": field_type or "unknown",
            "matched": value is not None,
            "normalized": False,
        }
        if field_type in {"regex", "regex_list"}:
            field_evidence["occurrence"] = field.get(
                "occurrence",
                "last",
            )
        if value is None:
            field_evidence["failure_reason"] = (
                "no_pattern_matched"
                if field_type == "regex_list"
                else "pattern_not_matched"
            )
        evidence[field_name] = field_evidence
    return evidence


def extract_collections_from_schemas_with_evidence(
    raw_text: str,
    collections: dict,
) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    extracted_collections = extract_collections_from_schemas(
        raw_text=raw_text,
        collections=collections,
    )

    collection_evidence = {}
    for collection_name, items in extracted_collections.items():
        collection_schema = collections.get(collection_name, {})
        fields = collection_schema.get("fields", [])
        generated_evidence = []

        start_pattern = collection_schema.get("start_pattern")
        if start_pattern is not None and fields:
            try:
                _, generated_evidence = (
                    extract_collection_from_schema_with_evidence(
                        raw_text=raw_text,
                        collection_schema=collection_schema,
                    )
                )
            except CollectionPipelineError:
                generated_evidence = []

        collection_evidence[collection_name] = [
            (
                generated_evidence[index]
                if index < len(generated_evidence)
                else build_collection_item_evidence(
                    item=item,
                    fields=fields,
                )
            )
            for index, item in enumerate(items)
        ]

    return extracted_collections, collection_evidence


def extract_collections_from_schemas(
    raw_text: str,
    collections: dict,
) -> dict[str, list[dict]]:
    if not isinstance(raw_text, str):
        raise CollectionPipelineError(
            "Raw text must be a string"
        )
    if not isinstance(collections, dict):
        raise CollectionPipelineError(
            "Collections must be an object"
        )

    extracted_collections: dict[str, list[dict]] = {}

    for collection_name, collection_schema in collections.items():
        if not isinstance(collection_name, str) or not collection_name:
            raise CollectionPipelineError(
                "Every collection must have a name"
            )
        if not isinstance(collection_schema, dict):
            raise CollectionPipelineError(
                f"Collection '{collection_name}' schema "
                "must be an object"
            )

        start_pattern = collection_schema.get("start_pattern")
        fields = collection_schema.get("fields")

        if start_pattern is None and fields == []:
            extracted_collections[collection_name] = []
            continue

        try:
            extracted_collections[collection_name] = (
                extract_collection_from_schema(
                    raw_text=raw_text,
                    collection_schema=collection_schema,
                )
            )
        except CollectionPipelineError as exc:
            raise CollectionPipelineError(
                f"Collection '{collection_name}' is invalid: {exc}"
            ) from exc

    return extracted_collections
