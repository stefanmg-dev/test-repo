from fastapi.testclient import TestClient

import routes_extract
from api import app


TEST_CONFIG = {
    "invoice": {
        "default_profile": "telecom_a1",
        "common_fields": [
            {
                "name": "supplier_name",
                "type": "constant",
                "value": "А1 България ЕАД",
                "validation": [],
            }
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "contract_number",
                        "type": "regex",
                        "rule": "([МM][0-9]+)",
                        "validation": [],
                    }
                ]
            }
        },
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


def test_extract_document_returns_selected_profile(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": (
                "Доставчик: А1 България ЕАД\n"
                "Договор M5781970"
            ),
            "quality": ACCEPTED_QUALITY,
        }

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: TEST_CONFIG,
    )

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
        data={
            "document_type": "invoice",
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

    body = response.json()

    assert body["document_type"] == "invoice"
    assert body["profile"] == "telecom_a1"

    assert body["final_values"] == {
        "supplier_name": "А1 България ЕАД",
        "contract_number": "M5781970",
    }

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }


def test_legacy_document_returns_no_profile(
    monkeypatch,
):
    legacy_config = {
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

    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": "Test OCR text",
            "quality": ACCEPTED_QUALITY,
        }

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: legacy_config,
    )

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
        data={
            "document_type": "invoice",
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

    body = response.json()

    assert body["document_type"] == "invoice"
    assert "profile" not in body

def test_unknown_supplier_uses_common_only_mode(
    monkeypatch,
):
    async def fake_extract_document_input(file):
        await file.read()

        return {
            "text": (
                "Софийска вода АД\n"
                "Фактура за предоставени услуги"
            ),
            "quality": ACCEPTED_QUALITY,
        }

    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: TEST_CONFIG,
    )

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
        data={
            "document_type": "invoice",
        },
        files={
            "file": (
                "unknown-supplier.png",
                b"fake-image-content",
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_type"] == "invoice"
    assert body["processing_status"] == "review"

    assert "profile" not in body

    assert body["final_values"] == {
        "supplier_name": "А1 България ЕАД",
    }

    assert "contract_number" not in (
        body["final_values"]
    )

    assert body["quality"] == {
        **ACCEPTED_QUALITY,
        "status": "review",
        "requires_review": True,
        "warnings": [
            {
                "code": (
                    "unknown_supplier_profile"
                ),
                "message": (
                    "No matching supplier profile "
                    "was found"
                ),
            }
        ],
    }

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }

