from collection_pipeline import extract_collection_from_schema
from config_store import load_config
from document_config_resolver import resolve_document_collections

TEXT = "Дневна 19 719 19 929 210 0 210\nНощна 3 991 4 051 60 0 60\nОбщо 270"

def schema():
    config = load_config()
    return resolve_document_collections(config["invoice"], "electricity_electrohold")["consumption_items"]

def test_schema_fields():
    assert [f["name"] for f in schema()["fields"]] == ["tariff", "previous_reading", "current_reading", "difference", "correction", "quantity", "unit"]

def test_extracts_original_tariff_rows():
    assert extract_collection_from_schema(TEXT, schema()) == [
        {"tariff":"Дневна","previous_reading":"19 719","current_reading":"19 929","difference":"210","correction":"0","quantity":"210","unit":"kWh"},
        {"tariff":"Нощна","previous_reading":"3 991","current_reading":"4 051","difference":"60","correction":"0","quantity":"60","unit":"kWh"},
    ]

def test_returns_empty_list_without_tariff_rows():
    assert extract_collection_from_schema("Общо 270", schema()) == []
