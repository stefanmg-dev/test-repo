from fastapi.testclient import TestClient

import routes_extract
from api import app


def test_unknown_document_type_returns_404_without_ocr(
    monkeypatch
):
    ocr_called = False

    async def fake_extract_text(file):
        nonlocal ocr_called

        ocr_called = True

        return "This function must not be called"

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: {
            "invoice": {
                "fields": [
                    {
                        "name": "invoice_number",
                        "type": "regex",
                        "rule": "([0-9]+)"
                    }
                ]
            }
        }
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_text",
        fake_extract_text
    )

    client = TestClient(app)

    response = client.post(
        "/extract-document",
        data={
            "document_type": "unknown"
        },
        files={
            "file": (
                "test.pdf",
                b"fake-pdf-content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Document type 'unknown' was not found"
        )
    }

    assert ocr_called is False


def test_empty_document_type_returns_409_without_ocr(
    monkeypatch
):
    ocr_called = False

    async def fake_extract_text(file):
        nonlocal ocr_called

        ocr_called = True

        return "This function must not be called"

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: {
            "draft": {
                "fields": []
            }
        }
    )

    monkeypatch.setattr(
        routes_extract,
        "extract_text",
        fake_extract_text
    )

    client = TestClient(app)

    response = client.post(
        "/extract-document",
        data={
            "document_type": "draft"
        },
        files={
            "file": (
                "test.pdf",
                b"fake-pdf-content",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": (
            "Document type 'draft' is not ready "
            "for extraction because it has no "
            "configured fields"
        )
    }

    assert ocr_called is False