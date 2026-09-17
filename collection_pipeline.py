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
