from fastapi.testclient import TestClient

import collection_pipeline
import routes_extract
from api import app


ELECTROHOLD_TEXT = """
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
""".strip()


PDF_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 1,
    },
    "warnings": [],
}


def test_endpoint_reports_invalid_electrical_collection_item(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": ELECTROHOLD_TEXT,
            "quality": PDF_QUALITY,
        }

    def fake_extract_collections_from_schemas(
        raw_text,
        collections,
    ):
        return {
            "services": [],
            "metering_points": [
                {
                    "metering_point_number": (
                        "32Z1030003158785"
                    ),
                }
            ],
            "meters": [
                {
                    "meter_number": "ABC",
                }
            ],
            "consumption_items": [
                {
                    "tariff": "Дневна",
                    "previous_reading": "19 719",
                    "current_reading": "19 929",
                    "difference": "210",
                    "correction": "0",
                    "quantity": "210",
                    "unit": "kWh",
                }
            ],
        }

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda raw_text: {},
    )
    monkeypatch.setattr(
        collection_pipeline,
        "extract_collections_from_schemas",
        fake_extract_collections_from_schemas,
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "electrohold-invalid-meter.pdf",
                b"electrohold-invalid-meter-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "electricity_electrohold"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    assert body["collection_validation"] == {
        "valid": False,
        "errors": {
            "meters[0].meter_number": [
                "Meter number is invalid",
            ]
        },
    }

    assert body["processing_status"] == "invalid"

    assert body["quality"] == PDF_QUALITY
    assert body["quality"]["requires_review"] is False

    assert body["collections"]["meters"] == [
        {
            "meter_number": "ABC",
        }
    ]


def test_endpoint_reports_invalid_consumption_quantity(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": ELECTROHOLD_TEXT,
            "quality": PDF_QUALITY,
        }

    def fake_extract_collections_from_schemas(
        raw_text,
        collections,
    ):
        return {
            "services": [],
            "metering_points": [
                {
                    "metering_point_number": (
                        "32Z1030003158785"
                    ),
                }
            ],
            "meters": [
                {
                    "meter_number": "1021015029",
                }
            ],
            "consumption_items": [
                {
                    "tariff": "Дневна",
                    "previous_reading": "19 719",
                    "current_reading": "19 929",
                    "difference": "210",
                    "correction": "0",
                    "quantity": "-1",
                    "unit": "kWh",
                }
            ],
        }

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda raw_text: {},
    )
    monkeypatch.setattr(
        collection_pipeline,
        "extract_collections_from_schemas",
        fake_extract_collections_from_schemas,
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "electrohold-invalid-quantity.pdf",
                b"electrohold-invalid-quantity-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "electricity_electrohold"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    assert body["collection_validation"] == {
        "valid": False,
        "errors": {
            "consumption_items[0].quantity": [
                (
                    "Consumption quantity must be "
                    "a non-negative decimal"
                ),
            ]
        },
    }

    assert body["processing_status"] == "invalid"

    assert body["quality"] == PDF_QUALITY
    assert body["quality"]["requires_review"] is False

    assert body["collections"][
        "consumption_items"
    ][0]["quantity"] == "-1"


import pytest


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
        "expected_message",
    ),
    [
        (
            "previous_reading",
            "19 A19",
            "Previous reading is invalid",
        ),
        (
            "correction",
            "-1",
            (
                "Consumption correction must be "
                "a non-negative decimal"
            ),
        ),
    ],
)
def test_endpoint_reports_invalid_consumption_numeric_field(
    monkeypatch,
    field_name,
    invalid_value,
    expected_message,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": ELECTROHOLD_TEXT,
            "quality": PDF_QUALITY,
        }

    consumption_item = {
        "tariff": "Дневна",
        "previous_reading": "19 719",
        "current_reading": "19 929",
        "difference": "210",
        "correction": "0",
        "quantity": "210",
        "unit": "kWh",
    }
    consumption_item[field_name] = invalid_value

    def fake_extract_collections_from_schemas(
        raw_text,
        collections,
    ):
        return {
            "services": [],
            "metering_points": [
                {
                    "metering_point_number": (
                        "32Z1030003158785"
                    ),
                }
            ],
            "meters": [
                {
                    "meter_number": "1021015029",
                }
            ],
            "consumption_items": [
                consumption_item,
            ],
        }

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )
    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda raw_text: {},
    )
    monkeypatch.setattr(
        collection_pipeline,
        "extract_collections_from_schemas",
        fake_extract_collections_from_schemas,
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "electrohold-invalid-consumption.pdf",
                b"electrohold-invalid-consumption-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "electricity_electrohold"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    error_path = (
        f"consumption_items[0].{field_name}"
    )

    assert body["collection_validation"] == {
        "valid": False,
        "errors": {
            error_path: [
                expected_message,
            ]
        },
    }

    assert body["processing_status"] == "invalid"
    assert body["quality"] == PDF_QUALITY

    returned_item = body["collections"][
        "consumption_items"
    ][0]

    assert returned_item[field_name] == invalid_value
