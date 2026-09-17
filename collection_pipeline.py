from collection_extractor import extract_collection_items
from collection_splitter import split_collection_blocks


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


class CollectionPipelineError(ValueError):
    pass


def extract_collection_from_schema(
    raw_text: str,
    collection_schema: dict,
) -> list[dict]:
    if not isinstance(collection_schema, dict):
        raise CollectionPipelineError(
            "Collection schema must be an object"
        )

    start_pattern = collection_schema.get(
        "start_pattern"
    )
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
