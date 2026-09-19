from fastapi.testclient import TestClient

import routes_extract
from api import app


UNKNOWN_SUPPLIER_OCR_TEXT = """
ДОСТАВЧИК: УНИВЕРСАЛЕН ДОСТАВЧИК ЕАД
ЕИК: 123456789

Фактура № 1200000001
Дата на издаване: 31.08.2026

Име: Тестов Клиент Примерен
Адрес: ж.к. Тестов комплекс, бл. 1, вх. А, ап. 1

Краен срок на плащане: 15.10.2026
Обща стойност за плащане 15,12
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


def test_unknown_supplier_uses_only_common_fields_and_requires_review(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": UNKNOWN_SUPPLIER_OCR_TEXT,
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
        lambda raw_text: {
            "supplier_name": "Универсален Доставчик ЕАД",
        },
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "unknown-supplier-invoice.pdf",
                b"unknown-supplier-stable-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_type"] == "invoice"
    assert body.get("profile") is None
    assert body["processing_status"] == "review"

    assert body["quality"]["status"] == "review"
    assert body["quality"]["requires_review"] is True

    warning_codes = {
        warning["code"]
        for warning in body["quality"]["warnings"]
    }
    assert "unknown_supplier_profile" in warning_codes

    final_values = body["final_values"]

    assert set(final_values) == {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "customer_name",
        "customer_address",
        "due_date",
        "total_amount",
    }

    assert final_values["supplier_name"] == (
        "Универсален Доставчик ЕАД"
    )
    assert final_values["supplier_id"] == "123456789"
    assert final_values["invoice_number"] == "1200000001"
    assert final_values["issue_date"] == "31.08.2026"
    assert final_values["due_date"] == "15.10.2026"
    assert final_values["total_amount"] == "15.12"

    assert "contract_number" not in final_values
    assert "client_number" not in final_values
    assert "abonat_number" not in final_values
    assert "business_partner_number" not in final_values
    assert "contract_account_number" not in final_values
    assert "installation_number" not in final_values
