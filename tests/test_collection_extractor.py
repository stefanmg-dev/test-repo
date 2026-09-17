import pytest

from collection_extractor import (
    CollectionExtractionError,
    extract_collection_items,
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


def test_extracts_one_meter_item():
    items = extract_collection_items(
        item_texts=[
            "Електромер № 1234567890 "
            "Потребление 87,50"
        ],
        fields=METER_FIELDS,
    )

    assert items == [
        {
            "meter_number": "1234567890",
            "consumption": "87.50",
            "unit": "kWh",
        }
    ]


def test_extracts_multiple_meter_items_in_order():
    items = extract_collection_items(
        item_texts=[
            (
                "Електромер №1111111111 "
                "Потребление 10,25"
            ),
            (
                "Фабричен номер 2222222222 "
                "Потребление 20.75"
            ),
        ],
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


def test_empty_collection_returns_empty_list():
    assert extract_collection_items(
        item_texts=[],
        fields=METER_FIELDS,
    ) == []


def test_missing_optional_value_is_none():
    items = extract_collection_items(
        item_texts=["Електромер №3333333333"],
        fields=METER_FIELDS,
    )

    assert items[0]["meter_number"] == "3333333333"
    assert items[0]["consumption"] is None


def test_rejects_unsupported_collection_field_type():
    with pytest.raises(
        CollectionExtractionError,
        match="Unsupported collection field type",
    ):
        extract_collection_items(
            item_texts=["sample"],
            fields=[
                {
                    "name": "meter_number",
                    "type": "llm",
                }
            ],
        )
