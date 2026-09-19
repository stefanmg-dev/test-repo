import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app


PDF_PATH_ENV = "ELECTROHOLD_REAL_PDF_PATH"


def get_real_pdf_path():
    configured_path = os.getenv(PDF_PATH_ENV)

    if not configured_path:
        pytest.skip(
            f"{PDF_PATH_ENV} is not configured"
        )

    pdf_path = Path(configured_path).expanduser()

    if not pdf_path.is_file():
        pytest.fail(
            f"Real Electrohold PDF was not found: {pdf_path}"
        )

    return pdf_path


def test_real_electrohold_collections_end_to_end(
    monkeypatch,
):
    pdf_path = get_real_pdf_path()

    monkeypatch.setattr(
        routes_extract,
        "extract_values",
        lambda raw_text: {},
    )

    with pdf_path.open("rb") as pdf_file:
        response = TestClient(app).post(
            "/extract-document",
            data={"document_type": "invoice"},
            files={
                "file": (
                    pdf_path.name,
                    pdf_file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["profile"] == "electricity_electrohold"
    assert body["processing_status"] == "accepted"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }
    assert body["collection_validation"] == {
        "valid": True,
        "errors": {},
    }

    assert body["collections"] == {
        "services": [],
        "metering_points": [
            {
                "metering_point_number": (
                    "32Z1030003158785"
                ),
            }
        ],
        "meters": [
            {
                "meter_number": "1021015029",
            }
        ],
        "consumption_items": [
            {
                "tariff": "Дневна",
                "previous_reading": "19 719",
                "current_reading": "19 929",
                "difference": "210",
                "correction": "0",
                "quantity": "210",
                "unit": "kWh",
            },
            {
                "tariff": "Нощна",
                "previous_reading": "3 991",
                "current_reading": "4 051",
                "difference": "60",
                "correction": "0",
                "quantity": "60",
                "unit": "kWh",
            },
        ],
    }

    assert body["quality"]["status"] == "accepted"
    assert body["quality"]["requires_review"] is False
