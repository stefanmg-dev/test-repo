from fastapi.testclient import TestClient

import routes_extract
from api import app


TEST_CONFIG = {
    "invoice": {
        "fields": [
            {
                "name": "supplier_name",
                "type": "constant",
                "value": "Test Supplier",
                "validation": [],
            }
        ]
    }
}


ACCEPTED_QUALITY = {
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


def test_extract_document_returns_input_quality(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        return {
            "text": "Test OCR text",
            "quality": ACCEPTED_QUALITY,
        }

    async def fake_extract_text(file):
        return "Test OCR text"

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: TEST_CONFIG,
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_text",
        fake_extract_text,
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_document_input",
        fake_extract_document_input,
        raising=False,
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda raw_text: {},
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_document_data",
        lambda **kwargs: {
            "fields": {
                "supplier_name": "Test Supplier"
            },
            "collections": {},
        },
    )

    monkeypatch.setattr(
        routes_extract,
        "validate_result",
        lambda **kwargs: {
            "valid": True,
            "errors": {},
        },
    )

    client = TestClient(app)

    response = client.post(
        "/extract-document",
        data={
            "document_type": "invoice"
        },
        files={
            "file": (
                "invoice.png",
                b"fake-image-content",
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["quality"] == (
        ACCEPTED_QUALITY
    )

    assert response_body["raw_text"] == (
        "Test OCR text"
    )

    assert response_body["final_values"] == {
        "supplier_name": "Test Supplier"
    }

    assert response_body["validation"] == {
        "valid": True,
        "errors": {},
    }