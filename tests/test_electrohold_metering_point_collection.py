from collection_pipeline import extract_collection_from_schema
from config_store import load_config
from document_config_resolver import resolve_document_collections


METERING_POINT_TEXT = (
    "Друга информация\n"
    "Точка на измерване 32Z1030003158785\n"
    "Предоставена мощност 8 кВт"
)


def get_metering_point_schema() -> dict:
    config = load_config()
    collections = resolve_document_collections(
        document_config=config["invoice"],
        profile_name="electricity_electrohold",
    )
    return collections["metering_points"]


def test_metering_point_schema_is_resolved():
    schema = get_metering_point_schema()

    assert schema["cardinality"] == "zero_or_more"
    assert schema["start_pattern"]
    assert [field["name"] for field in schema["fields"]] == [
        "metering_point_number"
    ]


def test_extracts_metering_point_from_original_invoice_text():
    items = extract_collection_from_schema(
        raw_text=METERING_POINT_TEXT,
        collection_schema=get_metering_point_schema(),
    )

    assert items == [
        {"metering_point_number": "32Z1030003158785"}
    ]


def test_metering_point_collection_supports_multiple_items():
    items = extract_collection_from_schema(
        raw_text=(
            "Точка на измерване 32Z1030003158785\n"
            "Точка на измерване 32Z1030003158786"
        ),
        collection_schema=get_metering_point_schema(),
    )

    assert items == [
        {"metering_point_number": "32Z1030003158785"},
        {"metering_point_number": "32Z1030003158786"},
    ]


def test_metering_point_collection_returns_empty_list():
    items = extract_collection_from_schema(
        raw_text="Фактура без точка на измерване",
        collection_schema=get_metering_point_schema(),
    )

    assert items == []
