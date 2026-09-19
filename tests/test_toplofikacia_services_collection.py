from collection_pipeline import extract_collection_from_schema
from config_store import load_config
from document_config_resolver import resolve_document_collections


SERVICES_TEXT = """
Наименование на стока / услуга Мярка Количество Ед.Цена Сума
Топлинна енергия за подгряване на вода МВтч 0,143953 73,30 10,55
Топлинна енергия за отопление на имот МВтч 0,000000 73,30 0,00
Дялово разпределение на топлинна енергия (1/12 част) бр 1 2,05 2,05
Авансово платени суми Евро 0,00
""".strip()


def get_services_schema():
    config = load_config()
    collections = resolve_document_collections(
        document_config=config["invoice"],
        profile_name="heating_toplofikacia_sofia",
    )
    return collections["services"]


def test_toplofikacia_services_schema_is_configured():
    schema = get_services_schema()
    assert schema["cardinality"] == "zero_or_more"
    assert [field["name"] for field in schema["fields"]] == [
        "description",
        "unit",
        "quantity",
        "unit_price",
        "amount",
    ]


def test_extracts_toplofikacia_services_in_order():
    assert extract_collection_from_schema(
        raw_text=SERVICES_TEXT,
        collection_schema=get_services_schema(),
    ) == [
        {
            "description": "Топлинна енергия за подгряване на вода",
            "unit": "МВтч",
            "quantity": "0.143953",
            "unit_price": "73.30",
            "amount": "10.55",
        },
        {
            "description": "Топлинна енергия за отопление на имот",
            "unit": "МВтч",
            "quantity": "0.000000",
            "unit_price": "73.30",
            "amount": "0.00",
        },
        {
            "description": (
                "Дялово разпределение на топлинна енергия "
                "(1/12 част)"
            ),
            "unit": "бр",
            "quantity": "1",
            "unit_price": "2.05",
            "amount": "2.05",
        },
    ]


def test_toplofikacia_services_returns_empty_list_without_rows():
    assert extract_collection_from_schema(
        raw_text="Фактура без редове за услуги",
        collection_schema=get_services_schema(),
    ) == []
