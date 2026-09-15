from fastapi.testclient import TestClient

import routes_extract
from api import app


A1_RAW_TEXT = """от 4
1
Стефан Момчилов Георгиев
София
19.08.2026
19.08.2026
М5781970
Адрес:
Имe:
Дата на дан. събитие:
Място на издаване:
Дата на издаване:
Договор №:
жк.Красно село бл.201А вх.Г ет.2 ап.68
1000 София
ПИН КОД ЗА ОНЛАЙН ПЛАЩАНЕ
1443
Фактура №0726592493
Период на фактуриране: 16.07.2026 - 15.08.2026
Обща стойност за плащане
67.96 €
Краен срок на плащане:
13.09.2026 г.

България ЕАД
A1
ЕИК:131468980 ДДС: BG131468980
Име: Адрес:
Стефан Момчилов Георгиев жк Красно село
Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493
"""


INVALID_RAW_TEXT = """А1 България ЕАД
от 4
1
Стефан Момчилов Георгиев
София
19.08.2026
19.08.2026
М5781970
Адрес:
Имe:
Дата на дан. събитие:
Място на издаване:
Дата на издаване:
Договор №:
жк.Красно село бл.201А вх.Г ет.2 ап.68
1000 София
Краен срок на плащане:
13.09.2026 г.
Обща стойност за плащане
67.96 €
"""


EXPECTED_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "contract_number": "М5781970",
    "customer_name": "Стефан Момчилов Георгиев",
    "customer_address": (
        "жк.Красно село бл.201А вх.Г ет.2 ап.68"
    ),
    "due_date": "13.09.2026",
    "total_amount": "67.96",
}


NATIVE_PDF_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 4,
    },
    "warnings": [],
}


async def fake_extract_document_input(file):
    await file.read()

    return {
        "text": A1_RAW_TEXT,
        "quality": NATIVE_PDF_QUALITY,
    }


async def fake_invalid_extract_document_input(
    file,
):
    await file.read()

    return {
        "text": INVALID_RAW_TEXT,
        "quality": NATIVE_PDF_QUALITY,
    }


def test_extract_document_endpoint(
    monkeypatch,
):
    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )

    client = TestClient(app)

    response = client.post(
        "/extract-document",
        data={
            "document_type": "invoice"
        },
        files={
            "file": (
                "a1-invoice.pdf",
                b"fake-pdf-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body[
        "document_type"
    ] == "invoice"

    assert response_body[
        "quality"
    ] == NATIVE_PDF_QUALITY

    assert response_body[
        "raw_text"
    ] == A1_RAW_TEXT

    assert response_body[
        "llm_values"
    ] == {}

    assert response_body[
        "final_values"
    ] == EXPECTED_VALUES

    assert response_body[
        "validation"
    ] == {
        "valid": True,
        "errors": {},
    }


def test_extract_document_reports_invalid_result(
    monkeypatch,
):
    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_invalid_extract_document_input,
    )

    client = TestClient(app)

    response = client.post(
        "/extract-document",
        data={
            "document_type": "invoice"
        },
        files={
            "file": (
                "incomplete-invoice.pdf",
                b"fake-pdf-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body[
        "quality"
    ] == NATIVE_PDF_QUALITY

    assert response_body[
        "raw_text"
    ] == INVALID_RAW_TEXT

    assert response_body[
        "validation"
    ][
        "valid"
    ] is False

    errors = response_body[
        "validation"
    ][
        "errors"
    ]

    assert "supplier_id" in errors
    assert "invoice_number" in errors