from collection_extractor import extract_collection_items
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
