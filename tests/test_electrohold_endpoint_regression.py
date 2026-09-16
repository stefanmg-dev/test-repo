from fastapi.testclient import TestClient

import routes_extract
from api import app


ELECTROHOLD_OCR_TEXT = """
ФАКТУРА № 0484935637 / 26.08.2026
ОРИГИНАЛ

Доставчик Електрохолд Продажби ЕАД
ЗДДС № BG175133827
Идент. № 175133827

Име СТЕФАН МОМЧИЛОВ ГЕОРГИЕВ
Адрес бул. БРАТЯ БЪКСТОН, бл. 201 А, вх. Г, ап. 68

Обща стойност на сделката 37,91 €
Срок за плащане на фактурата от 26.08.2026 до 09.09.2026

electrohold.bg/sales
""".strip()


PDF_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 2,
    },
    "warnings": [],
}


def test_electrohold_endpoint_selects_profile_skeleton(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": ELECTROHOLD_OCR_TEXT,
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

    client = TestClient(app)
    response = client.post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "electrohold-invoice.pdf",
                b"stable-electrohold-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_type"] == "invoice"
    assert body["profile"] == "electricity_electrohold"

    final_values = body["final_values"]

    assert len(final_values) == 8
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
        "Електрохолд Продажби ЕАД"
    )
    assert final_values["supplier_id"] == "175133827"
    assert final_values["invoice_number"] == "0484935637"
    assert final_values["issue_date"] == "26.08.2026"
    assert final_values["due_date"] == "09.09.2026"
    assert final_values["total_amount"] == "37.91"

    assert "contract_number" not in final_values

    warning_codes = {
        warning["code"]
        for warning in body["quality"]["warnings"]
    }
    assert "unknown_supplier_profile" not in warning_codes
