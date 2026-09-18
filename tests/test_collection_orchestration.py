import pytest

from collection_pipeline import (
    CollectionPipelineError,
    extract_collections_from_schemas,
)


COLLECTIONS = {
    "services": {
        "cardinality": "zero_or_more",
        "fields": [],
    },
    "metering_points": {
        "cardinality": "zero_or_more",
        "start_pattern": r"^Точка\s+на\s+измерване",
        "fields": [
            {
                "name": "metering_point_number",
                "type": "regex",
                "occurrence": "first",
                "rule": (
                    r"Точка\s+на\s+измерване\s+"
                    r"([0-9A-Z]{16})"
                ),
                "validation": [],
            }
        ],
    },
    "meters": {
        "cardinality": "zero_or_more",
        "start_pattern": r"^Електромер\s*№",
        "fields": [
            {
                "name": "meter_number",
                "type": "regex",
                "occurrence": "first",
                "rule": r"Електромер\s*№\s*([0-9]{8,15})",
                "validation": [],
            }
        ],
    },
    "consumption_items": {
        "cardinality": "zero_or_more",
        "start_pattern": r"^(?:Дневна|Нощна)\s+",
        "fields": [
            {
                "name": "tariff",
                "type": "regex",
                "occurrence": "first",
                "rule": r"^(Дневна|Нощна)\s+",
                "validation": [],
            }
        ],
    },
}


RAW_TEXT = (
    "Електромер № 1021015029\n"
    "Дневна 19 719 19 929 210 0 210\n"
    "Нощна 3 991 4 051 60 0 60\n"
    "Точка на измерване 32Z1030003158785"
)


def test_extracts_all_configured_collections():
    assert extract_collections_from_schemas(
        raw_text=RAW_TEXT,
        collections=COLLECTIONS,
    ) == {
        "services": [],
        "metering_points": [
            {
                "metering_point_number": "32Z1030003158785",
            }
        ],
        "meters": [
            {
                "meter_number": "1021015029",
            }
        ],
        "consumption_items": [
            {"tariff": "Дневна"},
            {"tariff": "Нощна"},
        ],
    }


def test_preserves_collection_order():
    result = extract_collections_from_schemas(
        raw_text=RAW_TEXT,
        collections=COLLECTIONS,
    )

    assert list(result) == list(COLLECTIONS)


def test_returns_empty_object_without_collections():
    assert extract_collections_from_schemas(
        raw_text=RAW_TEXT,
        collections={},
    ) == {}


def test_rejects_invalid_collections_container():
    with pytest.raises(
        CollectionPipelineError,
        match="Collections must be an object",
    ):
        extract_collections_from_schemas(
            raw_text=RAW_TEXT,
            collections=[],
        )


def test_reports_invalid_collection_name():
    with pytest.raises(
        CollectionPipelineError,
        match="Collection 'meters' is invalid",
    ):
        extract_collections_from_schemas(
            raw_text=RAW_TEXT,
            collections={
                "meters": {
                    "cardinality": "zero_or_more",
                    "fields": [{"name": "meter_number"}],
                }
            },
        )
