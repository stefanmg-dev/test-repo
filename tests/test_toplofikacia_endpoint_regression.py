from fastapi.testclient import TestClient

import routes_extract
from api import app


TOPLOFIKACIA_OCR_TEXT = """
ДОСТАВЧИК: „ТОПЛОФИКАЦИЯ СОФИЯ“ ЕАД
ЕИК: 123456789
№ ПО ДДС: BG123456789
www.toplo.bg

ПОЛУЧАТЕЛ: ТЕСТОВ КЛИЕНТ ПРИМЕРЕН
ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 АПАРТАМЕНТ 68
БИЗНЕС ПАРТНЬОР №1000000001
ДОГОВОРНА СМЕТКА №002100000001
НОМЕР НА ИНСТАЛАЦИЯ №4000000001

ФАКТУРА № 1200000001 - ОРИГИНАЛ
Дата на издаване/Дата на данъчно събитие - 31.08.2026 г.
ВСИЧКО по фактура: 15,12
Оставаща сума за плащане по фактура 1200000001 15,12 Евро
Срок за плащане на фактура № 1200000001 - 15.10.2026 г.
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


def test_toplofikacia_endpoint_selects_profile_and_returns_fields(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": TOPLOFIKACIA_OCR_TEXT,
            "quality": PDF_QUALITY,
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

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-invoice.pdf",
                b"stable-toplofikacia-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "invoice"
    assert body["profile"] == "heating_toplofikacia_sofia"

    final_values = body["final_values"]
    expected = {
        "supplier_name": "Топлофикация София ЕАД",
        "supplier_id": "123456789",
        "invoice_number": "1200000001",
        "issue_date": "31.08.2026",
        "customer_name": "ТЕСТОВ КЛИЕНТ ПРИМЕРЕН",
        "customer_address": (
            "ГР. СОФИЯ 1618 КРАСНО СЕЛО БЛ. 201-А ВХ. 4 "
            "АПАРТАМЕНТ 68"
        ),
        "due_date": "15.10.2026",
        "total_amount": "15.12",
        "business_partner_number": "1000000001",
        "contract_account_number": "002100000001",
        "installation_number": "4000000001",
    }
    assert final_values == expected

    warning_codes = {
        warning["code"]
        for warning in body["quality"]["warnings"]
    }
    assert "unknown_supplier_profile" not in warning_codes


def test_toplofikacia_endpoint_returns_accepted_validation(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": TOPLOFIKACIA_OCR_TEXT,
            "quality": PDF_QUALITY,
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

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-validation.pdf",
                b"stable-toplofikacia-validation-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "heating_toplofikacia_sofia"
    assert body["processing_status"] == "accepted"
    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }
    assert body["quality"]["status"] == "accepted"
    assert body["quality"]["requires_review"] is False


def test_toplofikacia_endpoint_is_invalid_when_required_field_is_missing(
    monkeypatch,
):
    incomplete_text = TOPLOFIKACIA_OCR_TEXT.replace(
        "НОМЕР НА ИНСТАЛАЦИЯ №4000000001\n",
        "",
    )

    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": incomplete_text,
            "quality": PDF_QUALITY,
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

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-missing-installation.pdf",
                b"toplofikacia-missing-installation-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "heating_toplofikacia_sofia"
    assert body["processing_status"] == "invalid"
    assert body["quality"]["status"] == "accepted"
    assert body["quality"]["requires_review"] is False

    assert body["final_values"]["installation_number"] is None
    assert body["validation"]["valid"] is False
    assert body["validation"]["errors"] == {
        "installation_number": [
            "Installation number is required",
        ]
    }


def test_toplofikacia_endpoint_returns_services_collection(
    monkeypatch,
):
    text_with_services = (
        TOPLOFIKACIA_OCR_TEXT
        + "\n"
        + "\n".join(
            [
                (
                    "Топлинна енергия за подгряване на вода "
                    "МВтч 0,143953 73,30 10,55"
                ),
                (
                    "Топлинна енергия за отопление на имот "
                    "МВтч 0,000000 73,30 0,00"
                ),
                (
                    "Дялово разпределение на топлинна енергия "
                    "(1/12 част) бр 1 2,05 2,05"
                ),
                "Авансово платени суми Евро 0,00",
            ]
        )
    )

    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": text_with_services,
            "quality": PDF_QUALITY,
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

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-services.pdf",
                b"stable-toplofikacia-services-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "heating_toplofikacia_sofia"
    assert body["processing_status"] == "accepted"

    assert body["collections"]["services"] == [
        {
            "description": (
                "Топлинна енергия за подгряване на вода"
            ),
            "unit": "МВтч",
            "quantity": "0.143953",
            "unit_price": "73.30",
            "amount": "10.55",
        },
        {
            "description": (
                "Топлинна енергия за отопление на имот"
            ),
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

    assert body["collections"]["metering_points"] == []
    assert body["collections"]["meters"] == []
    assert body["collections"]["consumption_items"] == []

    assert body["collection_validation"] == {
        "valid": True,
        "errors": {},
    }


def test_toplofikacia_endpoint_returns_services_collection(
    monkeypatch,
):
    text_with_services = (
        TOPLOFIKACIA_OCR_TEXT
        + "\n"
        + "\n".join(
            [
                (
                    "Топлинна енергия за подгряване на вода "
                    "МВтч 0,143953 73,30 10,55"
                ),
                (
                    "Топлинна енергия за отопление на имот "
                    "МВтч 0,000000 73,30 0,00"
                ),
                (
                    "Дялово разпределение на топлинна енергия "
                    "(1/12 част) бр 1 2,05 2,05"
                ),
                "Авансово платени суми Евро 0,00",
            ]
        )
    )

    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": text_with_services,
            "quality": PDF_QUALITY,
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

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "toplofikacia-services.pdf",
                b"stable-toplofikacia-services-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "heating_toplofikacia_sofia"
    assert body["processing_status"] == "accepted"

    assert body["collections"]["services"] == [
        {
            "description": (
                "Топлинна енергия за подгряване на вода"
            ),
            "unit": "МВтч",
            "quantity": "0.143953",
            "unit_price": "73.30",
            "amount": "10.55",
        },
        {
            "description": (
                "Топлинна енергия за отопление на имот"
            ),
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

    assert body["collections"]["metering_points"] == []
    assert body["collections"]["meters"] == []
    assert body["collections"]["consumption_items"] == []

    assert body["collection_validation"] == {
        "valid": True,
        "errors": {},
    }
