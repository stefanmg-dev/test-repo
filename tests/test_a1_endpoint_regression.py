import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app


PDF_OCR_TEXT = """
от 4
1
Стефан Момчилов Георгиев
София
19.08.2026
М5781970
Адрес:
Име:
Дата на издаване:
Договор №:
жк.Красно село бл.201А вх.Г ет.2 ап.68
1000 София
Фактура №0726592493
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
""".strip()


PNG_OCR_TEXT = """
"А1 България" ЕАД
ЕИК:131468980 ДДС: BG131468980

Име: Стефан Момчилов Георгиев
Адрес: жк Красно село бл.201А вх.Г ет 2 ап. 68 1000 София

Дата на издаване: 19.08.2026
Договор Ng: M5781970
Фактура Ng0726592493

Обща стойност за плащане
67.96 €

Краен срок на плащане: 13.09.2026 г.
""".strip()


PDF_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PDF",
        "source": "native_pdf",
        "page_count": 4,
    },
    "warnings": [],
}


PNG_QUALITY = {
    "status": "accepted",
    "requires_review": False,
    "input": {
        "format": "PNG",
        "width": 1447,
        "height": 2048,
        "short_edge": 1447,
        "long_edge": 2048,
        "pixel_count": 2963456,
        "mode": "RGBA",
    },
    "warnings": [],
}


EXPECTED_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "contract_number": "M5781970",
    "customer_name": "Стефан Момчилов Георгиев",
    "customer_address": (
        "жк Красно село бл.201А вх.Г ет 2 ап. 68"
    ),
    "due_date": "13.09.2026",
    "total_amount": "67.96",
}


@pytest.mark.parametrize(
    (
        "filename",
        "content_type",
        "raw_text",
        "quality",
    ),
    [
        (
            "a1-invoice.pdf",
            "application/pdf",
            PDF_OCR_TEXT,
            PDF_QUALITY,
        ),
        (
            "a1-invoice.png",
            "image/png",
            PNG_OCR_TEXT,
            PNG_QUALITY,
        ),
    ],
)
def test_a1_pdf_and_png_endpoint_regression(
    monkeypatch,
    filename,
    content_type,
    raw_text,
    quality,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": raw_text,
            "quality": quality,
        }

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda text: {},
    )

    client = TestClient(app)

    response = client.post(
        "/extract-document",
        data={
            "document_type": "invoice",
        },
        files={
            "file": (
                filename,
                b"stable-regression-fixture",
                content_type,
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_type"] == "invoice"
    assert body["profile"] == "telecom_a1"
    assert body["processing_status"] == "accepted"
    assert body["quality"] == quality
    final_values = body["final_values"]

    assert len(final_values) == 9
    assert set(final_values) == set(
        EXPECTED_VALUES
    )

    stable_field_names = {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "customer_name",
        "due_date",
        "total_amount",
    }

    for field_name in stable_field_names:
        assert final_values[field_name] == (
            EXPECTED_VALUES[field_name]
        )

    assert final_values[
        "contract_number"
    ] in {
        "M5781970",
        "М5781970",
    }

    assert final_values[
        "customer_address"
    ] in {
        (
            "жк Красно село "
            "бл.201А вх.Г ет 2 ап. 68"
        ),
        (
            "жк.Красно село "
            "бл.201А вх.Г ет.2 ап.68"
        ),
    }

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

    warning_codes = {
        warning["code"]
        for warning in body["quality"]["warnings"]
    }

    assert (
        "unknown_supplier_profile"
        not in warning_codes
    )
