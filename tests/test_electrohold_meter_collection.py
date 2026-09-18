from collection_pipeline import extract_collection_from_schema
from config_store import load_config
from document_config_resolver import resolve_document_collections


ELECTROHOLD_METER_TEXT = (
    "Консумирана електрическа енергия\n"
    "Електромер № 1021015029\n"
    "Старо показание Ново показание Разлика "
    "Корекция Колич. (кВтч)\n"
    "Дневна 19 719 19 929 210 0 210\n"
    "Нощна 3 991 4 051 60 0 60\n"
    "Общо 270"
)


def get_electrohold_meter_schema() -> dict:
    config = load_config()
    collections = resolve_document_collections(
        document_config=config["invoice"],
        profile_name="electricity_electrohold",
    )
    return collections["meters"]


def test_electrohold_meter_schema_is_resolved():
    schema = get_electrohold_meter_schema()

    assert schema["cardinality"] == "zero_or_more"
    assert schema["start_pattern"]
    assert [field["name"] for field in schema["fields"]] == [
        "meter_number"
    ]


def test_extracts_meter_number_from_original_invoice_text():
    items = extract_collection_from_schema(
        raw_text=ELECTROHOLD_METER_TEXT,
        collection_schema=get_electrohold_meter_schema(),
    )

    assert items == [
        {
            "meter_number": "1021015029",
        }
    ]


def test_electrohold_meter_collection_supports_multiple_meters():
    items = extract_collection_from_schema(
        raw_text=(
            "Електромер № 1021015029\n"
            "Дневна 210\n"
            "Електромер № 9876543210\n"
            "Дневна 100"
        ),
        collection_schema=get_electrohold_meter_schema(),
    )

    assert items == [
        {"meter_number": "1021015029"},
        {"meter_number": "9876543210"},
    ]


def test_electrohold_meter_collection_returns_empty_list():
    items = extract_collection_from_schema(
        raw_text="Фактура без данни за електромер",
        collection_schema=get_electrohold_meter_schema(),
    )

    assert items == []
