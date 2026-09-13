import re
from typing import Any

from document_config_resolver import resolve_document_fields


def clean_value(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, tuple):
        value = value[-1]

    value = str(value).strip()

    return value or None


def select_match(matches: list, occurrence: str) -> str | None:
    if not matches:
        return None

    if occurrence == "first":
        selected = matches[0]
    else:
        selected = matches[-1]

    return clean_value(selected)


def extract_regex_value(
    text: str,
    pattern: str,
    occurrence: str = "last"
) -> str | None:
    if not pattern:
        return None

    matches = re.findall(
        pattern,
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return select_match(matches, occurrence)


def extract_nearby_value(
    raw_text: str,
    anchor: str,
    pattern: str,
    occurrence: str = "last",
    direction: str = "both",
    window_size: int = 400
) -> str | None:
    if not anchor or not pattern:
        return None

    anchor_match = re.search(
        re.escape(anchor),
        raw_text,
        flags=re.IGNORECASE
    )

    if not anchor_match:
        return None

    anchor_start = anchor_match.start()
    anchor_end = anchor_match.end()

    if direction == "before":
        window_start = max(0, anchor_start - window_size)
        window_end = anchor_start

    elif direction == "after":
        window_start = anchor_end
        window_end = min(len(raw_text), anchor_end + window_size)

    else:
        window_start = max(0, anchor_start - window_size)
        window_end = min(len(raw_text), anchor_end + window_size)

    window = raw_text[window_start:window_end]

    return extract_regex_value(
        text=window,
        pattern=pattern,
        occurrence=occurrence
    )


def apply_rules(
    document_type: str,
    config: dict,
    raw_text: str,
    llm_values: dict
):
    doc_cfg = config.get(document_type)

    if not doc_cfg:
        return {
            "error": f"Unknown document type: {document_type}"
        }

    fields = resolve_document_fields(
        doc_cfg
    )

    final_values = {}

    for field in fields:
        field_name = field.get("name")
        field_type = field.get("type")

        if not field_name:
            continue

        if field_type == "llm":
            final_values[field_name] = llm_values.get(field_name)

        elif field_type == "constant":
            final_values[field_name] = clean_value(
                field.get("value")
            )

        elif field_type == "regex":
            final_values[field_name] = extract_regex_value(
                text=raw_text,
                pattern=field.get("rule", ""),
                occurrence=field.get("occurrence", "last")
            )

        elif field_type == "regex_list":
            final_values[field_name] = None

            for pattern in field.get("rules", []):
                value = extract_regex_value(
                    text=raw_text,
                    pattern=pattern,
                    occurrence=field.get("occurrence", "last")
                )

                if value is not None:
                    final_values[field_name] = value
                    break

        elif field_type == "nearby":
            final_values[field_name] = extract_nearby_value(
                raw_text=raw_text,
                anchor=field.get("anchor", ""),
                pattern=field.get("pattern", ""),
                occurrence=field.get("occurrence", "last"),
                direction=field.get("direction", "both"),
                window_size=field.get("window_size", 400)
            )

        else:
            final_values[field_name] = None

    return final_values