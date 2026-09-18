from fastapi.testclient import TestClient

import routes_extract
from api import app


def test_endpoint_uses_document_engine_without_changing_response(
    monkeypatch,
):
    raw_text = (
        "ФАКТУРА № 0484935637 / 26.08.2026\n"
        "Електрохолд Продажби ЕАД electrohold.bg/sales"
    )
    quality = {
        "status": "accepted",
        "requires_review": False,
        "input": {
            "format": "PDF",
            "source": "native_pdf",
            "page_count": 1,
        },
        "warnings": [],
    }
    engine_calls = []

    async def fake_extract_document_input(file):
        await file.read()
        return {"text": raw_text, "quality": quality}

    def fake_extract_document_data(**kwargs):
        engine_calls.append(kwargs)
        return {
            "fields": {
                "supplier_name": "Електрохолд Продажби ЕАД",
                "invoice_number": "0484935637",
            },
            "collections": {
                "services": [],
                "meters": [
                    {"meter_number": "1021015029"}
                ],
            },
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
    monkeypatch.setattr(
        routes_extract,
        "extract_document_data",
        fake_extract_document_data,
    )
    monkeypatch.setattr(
        routes_extract,
        "validate_result",
        lambda **kwargs: {"valid": True, "errors": {}},
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "electrohold.pdf",
                b"stable-fixture",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert len(engine_calls) == 1
    assert engine_calls[0]["profile_name"] == (
        "electricity_electrohold"
    )
    assert engine_calls[0]["resolved_fields"] is not None

    body = response.json()
    assert body["final_values"] == {
        "supplier_name": "Електрохолд Продажби ЕАД",
        "invoice_number": "0484935637",
    }
    assert "collections" not in body
