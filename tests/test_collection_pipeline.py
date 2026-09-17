import pytest

from collection_pipeline import (
    CollectionPipelineError,
    extract_collection_from_schema,
    extract_collection_from_text,
)


METER_START_PATTERN = (
    r"^(?:Електромер\s*№|Фабричен\s+номер)"
)

METER_FIELDS = [
    {
        "name": "meter_number",
        "type": "regex_list",
        "occurrence": "first",
        "rules": [
            r"Електромер\s*№\s*([0-9]{8,15})",
            r"Фабричен\s+номер\s*([0-9]{8,15})",
        ],
        "validation": [],
    },
    {
        "name": "consumption",
        "type": "regex",
        "rule": r"Потребление\s*([0-9]+[.,][0-9]+)",
        "occurrence": "last",
        "validation": [
            {
                "type": "decimal",
                "minimum": "0",
            }
        ],
    },
    {
        "name": "unit",
        "type": "constant",
        "value": "kWh",
        "validation": [],
    },
]


def test_pipeline_returns_empty_list_without_items():
    items = extract_collection_from_text(
        raw_text="Фактура без електромери",
        start_pattern=METER_START_PATTERN,
        fields=METER_FIELDS,
    )

    assert items == []


def test_pipeline_extracts_one_item():
    items = extract_collection_from_text(
        raw_text=(
            "Данни за фактурата\n"
            "Електромер №1234567890\n"
            "Потребление 87,50"
        ),
        start_pattern=METER_START_PATTERN,
        fields=METER_FIELDS,
    )

    assert items == [
        {
            "meter_number": "1234567890",
            "consumption": "87.50",
            "unit": "kWh",
        }
    ]


def test_pipeline_extracts_multiple_items_in_order():
    items = extract_collection_from_text(
        raw_text=(
            "Данни за клиента\n"
            "Електромер №1111111111\n"
            "Потребление 10,25\n"
            "Фабричен номер 2222222222\n"
            "Потребление 20.75"
        ),
        start_pattern=METER_START_PATTERN,
        fields=METER_FIELDS,
    )

    assert items == [
        {
            "meter_number": "1111111111",
            "consumption": "10.25",
            "unit": "kWh",
        },
        {
            "meter_number": "2222222222",
            "consumption": "20.75",
            "unit": "kWh",
        },
    ]


def test_pipeline_keeps_missing_optional_values():
    items = extract_collection_from_text(
        raw_text=(
            "Електромер №3333333333\n"
            "Бележка без потребление"
        ),
        start_pattern=METER_START_PATTERN,
        fields=METER_FIELDS,
    )

    assert items == [
        {
            "meter_number": "3333333333",
            "consumption": None,
            "unit": "kWh",
        }
    ]


def test_schema_pipeline_extracts_multiple_items():
    schema = {
        "cardinality": "zero_or_more",
        "start_pattern": METER_START_PATTERN,
        "fields": METER_FIELDS,
    }

    items = extract_collection_from_schema(
        raw_text=(
            "Електромер №1111111111\n"
            "Потребление 10,25\n"
            "Фабричен номер 2222222222\n"
            "Потребление 20.75"
        ),
        collection_schema=schema,
    )

    assert [item["meter_number"] for item in items] == [
        "1111111111",
        "2222222222",
    ]


def test_schema_pipeline_returns_empty_list():
    assert extract_collection_from_schema(
        raw_text="Фактура без електромери",
        collection_schema={
            "cardinality": "zero_or_more",
            "start_pattern": METER_START_PATTERN,
            "fields": METER_FIELDS,
        },
    ) == []


def test_schema_pipeline_rejects_missing_start_pattern():
    with pytest.raises(
        CollectionPipelineError,
        match="start_pattern",
    ):
        extract_collection_from_schema(
            raw_text="sample",
            collection_schema={
                "cardinality": "zero_or_more",
                "fields": [],
            },
        )
