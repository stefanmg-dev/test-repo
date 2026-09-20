import copy

from config_store import load_config
from extraction_orchestrator import (
    extract_document_data,
)


TEXT = """
ФАКТУРА № 0484935637 / 26.08.2026
Доставчик Електрохолд Продажби ЕАД
ЗДДС № BG175133827
Идент. № 175133827
Име ТЕСТОВ КЛИЕНТ ПРИМЕРЕН
Адрес бул. ТЕСТОВ, бл. 1, вх. А, ап. 1
Обща стойност на сделката 37,91
Срок за плащане на фактурата от 26.08.2026 до 09.09.2026
КЛИЕНТСКИ НОМЕР 300000000001
Абонатен № 9000000001
electrohold.bg/sales

Дневна
19 719
19 929
210
0
210
Нощна
3 991
4 051
60
0
60
Общо
270
Снабдяване/Разпределение с електрическа енергия
""".strip()


def extract(text):
    config = copy.deepcopy(load_config())

    return extract_document_data(
        document_type="invoice",
        config=config,
        raw_text=text,
        llm_values={},
        profile_name="electricity_electrohold",
    )


def test_extracts_total_consumption():
    result = extract(TEXT)

    assert result["fields"][
        "total_consumption"
    ] == "270"


def test_total_consumption_does_not_match_money_total():
    text = TEXT.replace(
        "Общо\n270\nСнабдяване/Разпределение",
        "Общо количество липсва",
    )

    result = extract(text)

    assert result["fields"][
        "total_consumption"
    ] is None


def test_total_consumption_is_not_a_collection_item():
    result = extract(TEXT)

    assert result["collections"][
        "consumption_items"
    ] == [
        {
            "tariff": "Дневна",
            "previous_reading": "19 719",
            "current_reading": "19 929",
            "difference": "210",
            "correction": "0",
            "quantity": "210",
            "unit": "kWh",
        },
        {
            "tariff": "Нощна",
            "previous_reading": "3 991",
            "current_reading": "4 051",
            "difference": "60",
            "correction": "0",
            "quantity": "60",
            "unit": "kWh",
        },
    ]
