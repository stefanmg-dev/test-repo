from config_store import load_config
from extraction_orchestrator import extract_document_data


ELECTROHOLD_INVOICE_TEXT = (
    "ФАКТУРА № 0484935637 / 26.08.2026 ОРИГИНАЛ\n"
    "Доставчик Електрохолд Продажби ЕАД\n"
    "ЗДДС № BG175133827 Идент. № 175133827\n"
    "Име СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ Адрес "
    "бул. БРАТЯ БЪКСТОН, бл. 201 А, вх. Г, ап. 68\n"
    "Консумирана електрическа енергия\n"
    "Електромер № 1021015029\n"
    "Старо показание Ново показание Разлика "
    "Корекция Колич. (кВтч)\n"
    "Дневна 19 719 19 929 210 0 210\n"
    "Нощна 3 991 4 051 60 0 60\n"
    "Общо 270\n"
    "Обща стойност на сделката 37,91\n"
    "Точка на измерване 32Z1030003158785\n"
    "Абонатен № 9430804222\n"
    "КЛИЕНТСКИ НОМЕР 300031587847\n"
    "Срок за плащане на фактурата от 26.08.2026 "
    "до 09.09.2026"
)


def extract_electrohold_invoice() -> dict:
    return extract_document_data(
        document_type="invoice",
        config=load_config(),
        raw_text=ELECTROHOLD_INVOICE_TEXT,
        llm_values={},
        profile_name="electricity_electrohold",
    )


def test_real_electrohold_text_extracts_scalar_fields():
    fields = extract_electrohold_invoice()["fields"]

    assert fields["supplier_name"] == "Електрохолд Продажби ЕАД"
    assert fields["supplier_id"] == "175133827"
    assert fields["invoice_number"] == "0484935637"
    assert fields["issue_date"] == "26.08.2026"
    assert fields["due_date"] == "09.09.2026"
    assert fields["total_amount"] == "37.91"
    assert fields["client_number"] == "300031587847"
    assert fields["abonat_number"] == "9430804222"


def test_real_electrohold_text_extracts_all_collections():
    collections = extract_electrohold_invoice()["collections"]

    assert collections["services"] == []
    assert collections["metering_points"] == [
        {"metering_point_number": "32Z1030003158785"}
    ]
    assert collections["meters"] == [
        {"meter_number": "1021015029"}
    ]
    assert collections["consumption_items"] == [
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


def test_engine_result_keeps_fields_and_collections_separate():
    result = extract_electrohold_invoice()

    assert set(result) == {"fields", "collections"}
    assert "meters" not in result["fields"]
    assert "invoice_number" not in result["collections"]
