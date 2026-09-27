import logging

from fastapi.testclient import TestClient

import routes_extract
from api import app


def test_invoice_shadow_validation_calls_mapper(monkeypatch):
    calls = []

    def mapper(**kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        routes_extract,
        "map_extraction_to_universal_invoice",
        mapper,
    )

    result = routes_extract.validate_universal_invoice_shadow(
        document_type="invoice",
        final_values={"invoice_number": "INV-1"},
        collections={"services": []},
    )

    assert result is True
    assert calls == [
        {
            "document_type": "invoice",
            "final_values": {"invoice_number": "INV-1"},
            "collections": {"services": []},
        }
    ]


def test_invoice_shadow_validation_failure_is_non_blocking(
    monkeypatch,
    caplog,
):
    def fail_mapper(**kwargs):
        raise ValueError("document values must not be logged")

    monkeypatch.setattr(
        routes_extract,
        "map_extraction_to_universal_invoice",
        fail_mapper,
    )

    with caplog.at_level(
        logging.WARNING,
        logger="document_processing.extraction",
    ):
        result = routes_extract.validate_universal_invoice_shadow(
            document_type="invoice",
            final_values={"invoice_number": "PRIVATE-1"},
            collections={},
        )

    assert result is False
    record = next(
        record
        for record in caplog.records
        if getattr(record, "event", None)
        == "invoice.shadow_validation_failed"
    )
    assert record.error_type == "ValueError"
    assert "PRIVATE-1" not in record.getMessage()
    assert "document values must not be logged" not in (
        record.getMessage()
    )


def test_non_invoice_shadow_validation_skips_mapper(monkeypatch):
    def unexpected_mapper(**kwargs):
        raise AssertionError("Mapper must not be called")

    monkeypatch.setattr(
        routes_extract,
        "map_extraction_to_universal_invoice",
        unexpected_mapper,
    )

    result = routes_extract.validate_universal_invoice_shadow(
        document_type="receipt",
        final_values={},
        collections={},
    )

    assert result is None


def test_invoice_endpoint_survives_shadow_validation_failure(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()
        return {
            "text": "Test OCR text",
            "quality": {
                "status": "accepted",
                "requires_review": False,
                "input": {
                    "format": "PDF",
                    "source": "native_pdf",
                    "page_count": 1,
                },
                "warnings": [],
            },
        }

    config = {
        "invoice": {
            "fields": [
                {
                    "name": "invoice_number",
                    "type": "constant",
                    "value": "INV-1",
                    "validation": [],
                }
            ]
        }
    }
    monkeypatch.setattr(routes_extract, "load_config", lambda: config)
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
        routes_extract,
        "map_extraction_to_universal_invoice",
        lambda **kwargs: (_ for _ in ()).throw(
            ValueError("shadow failure")
        ),
    )

    response = TestClient(app).post(
        "/extract-document",
        data={"document_type": "invoice"},
        files={
            "file": (
                "invoice.pdf",
                b"content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["final_values"]["invoice_number"] == (
        "INV-1"
    )
    assert "universal_invoice" not in response.json()
