import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app


QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 1,
    },
    "warnings": [],
}


A1_TEXT = """
А1 България ЕАД
ЕИК: 131468980
Фактура №0726592493
Дата на издаване: 19.08.2026
Име: Тестов Клиент Примерен
Адрес: жк. Тестов комплекс, бл. 1, ап. 1
Краен срок на плащане: 13.09.2026
Обща стойност за плащане 67.96
Договор № M5781970

Топлинна енергия за отопление МВтч 1,00 70,00 70,00
Електромер №1234567890
Точка на измерване 32Z0000000000001
Дневна 100 200 100 0 100
""".strip()


ELECTROHOLD_TEXT = """
ФАКТУРА № 0484935637 / 26.08.2026
Доставчик Електрохолд Продажби ЕАД
ЗДДС № BG175133827
Идент. № 175133827
Име ТЕСТОВ КЛИЕНТ ПРИМЕРЕН
Адрес жк. ТЕСТОВ, бл. 1, вх. А, ап. 1
Обща стойност на сделката 37,91
Срок за плащане на фактурата от 26.08.2026 до 09.09.2026
КЛИЕНТСКИ НОМЕР 300000000001
Абонатен № 9000000001
electrohold.bg/sales

Топлинна енергия за отопление МВтч 1,00 70,00 70,00
""".strip()


TOPLOFIKACIA_TEXT = """
ТОПЛОФИКАЦИЯ СОФИЯ ЕАД
ЕИК: 831609046
www.toplo.bg
ПОЛУЧАТЕЛ: ТЕСТОВ КЛИЕНТ ПРИМЕРЕН
ГР. СОФИЯ 1000 ТЕСТОВ КВАРТАЛ БЛ. 1 ВХ. А АПАРТАМЕНТ 1
БИЗНЕС ПАРТНЬОР №1000000001
ДОГОВОРНА СМЕТКА №002100000001
НОМЕР НА ИНСТАЛАЦИЯ №4000000001
ФАКТУРА № 1200000001 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026
ВСИЧКО по фактура: 15,12
Срок за плащане на фактура № 1200000001 - 15.10.2026

Топлинна енергия за отопление МВтч 1,00 13,07 13,07
Дялово разпределение бр 1 2,05 2,05

Електромер №1234567890
Точка на измерване 32Z0000000000001
Дневна 100 200 100 0 100
""".strip()


UNKNOWN_TEXT = """
ДОСТАВЧИК: УНИВЕРСАЛЕН ДОСТАВЧИК ЕАД
ЕИК: 123456789
Фактура № 1200000001
Дата на издаване: 31.08.2026
Име: Тестов Клиент Примерен
Адрес: ж.к. Тестов комплекс, бл. 1, вх. А, ап. 1
Краен срок на плащане: 15.10.2026
Обща стойност за плащане 15,12

Топлинна енергия за отопление МВтч 1,00 13,07 13,07
Електромер №1234567890
Точка на измерване 32Z0000000000001
Дневна 100 200 100 0 100
""".strip()


@pytest.mark.parametrize(
    (
        "raw_text",
        "expected_profile",
        "expected_empty_collections",
    ),
    [
        (
            A1_TEXT,
            "telecom_a1",
            {
                "services",
                "metering_points",
                "meters",
                "consumption_items",
            },
        ),
        (
            ELECTROHOLD_TEXT,
            "electricity_electrohold",
            {
                "services",
            },
        ),
        (
            TOPLOFIKACIA_TEXT,
            "heating_toplofikacia_sofia",
            {
                "metering_points",
                "meters",
                "consumption_items",
            },
        ),
        (
            UNKNOWN_TEXT,
            None,
            {
                "services",
                "metering_points",
                "meters",
                "consumption_items",
            },
        ),
    ],
)
def test_endpoint_does_not_leak_foreign_collections(
    monkeypatch,
    raw_text,
    expected_profile,
    expected_empty_collections,
):
    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": raw_text,
            "quality": QUALITY,
        }

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda text: {
            "supplier_name": "Универсален Доставчик ЕАД",
        }
        if text == UNKNOWN_TEXT
        else {},
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "collection-isolation.pdf",
                b"collection-isolation-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body.get("profile") == expected_profile
    assert set(body["collections"]) == {
        "services",
        "metering_points",
        "meters",
        "consumption_items",
    }

    for collection_name in expected_empty_collections:
        assert body["collections"][collection_name] == []

    if expected_profile == "heating_toplofikacia_sofia":
        assert len(body["collections"]["services"]) == 2

    if expected_profile is None:
        warning_codes = {
            warning["code"]
            for warning in body["quality"]["warnings"]
        }
        assert "unknown_supplier_profile" in warning_codes
        assert body["quality"]["requires_review"] is True
