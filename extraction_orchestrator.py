import re
from typing import Any

from document_config_resolver import (
    resolve_document_collections,
    resolve_document_fields,
)


def clean_value(value: Any) -> str | None:
    if value is None:
        return None

    if isinstance(value, tuple):
        value = value[-1]

    value = re.sub(
        r"\s+",
        " ",
        str(value),
    ).strip()

    return value or None


def select_match(matches: list, occurrence: str) -> str | None:
    if not matches:
        return None

    if occurrence == "first":
        selected = matches[0]
    else:
        selected = matches[-1]

    return clean_value(selected)


def has_decimal_validation(
    field: dict,
) -> bool:
    return any(
        isinstance(validation, dict)
        and validation.get("type") == "decimal"
        for validation in field.get(
            "validation",
            [],
        )
    )


def normalize_field_value(
    field: dict,
    value,
):
    if (
        isinstance(value, str)
        and has_decimal_validation(field)
        and re.fullmatch(
            r"[0-9]+,[0-9]+",
            value,
        )
    ):
        return value.replace(",", ".", 1)

    return value


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
    llm_values: dict,
    resolved_fields: list[dict] | None = None,
):
    doc_cfg = config.get(document_type)

    if not doc_cfg:
        return {
            "error": f"Unknown document type: {document_type}"
        }

    fields = resolved_fields

    if fields is None:
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

    for field in fields:
        field_name = field.get("name")

        if not field_name:
            continue

        final_values[field_name] = (
            normalize_field_value(
                field=field,
                value=final_values.get(
                    field_name
                ),
            )
        )

    return final_values


def extract_document_data(
    document_type: str,
    config: dict,
    raw_text: str,
    llm_values: dict,
    profile_name: str | None = None,
    resolved_fields: list[dict] | None = None,
) -> dict:
    document_config = config.get(document_type)
    if not document_config:
        return {
            "error": f"Unknown document type: {document_type}"
        }

    fields_for_extraction = resolved_fields
    if fields_for_extraction is None:
        fields_for_extraction = resolve_document_fields(
            document_config=document_config,
            profile_name=profile_name,
        )

    fields = apply_rules(
        document_type=document_type,
        config=config,
        raw_text=raw_text,
        llm_values=llm_values,
        resolved_fields=fields_for_extraction,
    )
    collections = resolve_document_collections(
        document_config=document_config,
        profile_name=profile_name,
    )

    # Delayed import breaks the pre-existing dependency cycle:
    # collection_pipeline -> collection_extractor -> this module.
    from collection_pipeline import (
        extract_collections_from_schemas,
    )

    extracted_collections = extract_collections_from_schemas(
        raw_text=raw_text,
        collections=collections,
    )

    from collection_validator import validate_collections

    return {
        "fields": fields,
        "collections": extracted_collections,
        "collection_validation": validate_collections(
            collections=extracted_collections,
            collection_schemas=collections,
        ),
    }
