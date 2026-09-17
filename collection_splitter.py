import re


class CollectionSplitError(ValueError):
    pass


def split_collection_blocks(
    raw_text: str,
    start_pattern: str,
) -> list[str]:
    if not isinstance(raw_text, str):
        raise CollectionSplitError(
            "Collection source text must be a string"
        )
    if not isinstance(start_pattern, str) or not start_pattern:
        raise CollectionSplitError(
            "Collection start pattern must be a non-empty string"
        )

    try:
        matches = list(
            re.finditer(
                start_pattern,
                raw_text,
                flags=re.IGNORECASE | re.MULTILINE,
            )
        )
    except re.error as exc:
        raise CollectionSplitError(
            f"Invalid collection start pattern: {exc}"
        ) from exc

    blocks = []

    for index, match in enumerate(matches):
        block_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(raw_text)
        )
        block = raw_text[match.start():block_end].strip()

        if block:
            blocks.append(block)

    return blocks
