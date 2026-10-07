import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app
from config_store import load_config


PDF_PATH_ENV = "A1_REAL_PDF_PATH"


def get_real_pdf_path() -> Path:
    configured_path = os.getenv(PDF_PATH_ENV)
    if not configured_path:
        pytest.skip(f"{PDF_PATH_ENV} is not configured")

    pdf_path = Path(configured_path).expanduser()
    if not pdf_path.is_file():
        pytest.fail("Configured real A1 PDF was not found")
    return pdf_path


def test_real_a1_pdf_end_to_end(monkeypatch):
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
                    "manual-a1-regression.pdf",
                    pdf_file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["document_type"] == "invoice"
    assert body["profile"] == "telecom_a1"
    assert body["processing_status"] == "accepted"
    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }
    assert body["collection_validation"] == {
        "valid": True,
        "errors": {},
    }

    invoice = load_config()["invoice"]
    profile = invoice["profiles"][body["profile"]]
    expected_field_names = {
        field["name"]
        for field in [
            *invoice.get("common_fields", []),
            *profile.get("fields", []),
        ]
    }
    final_values = body["final_values"]
    assert set(final_values) == expected_field_names
    assert all(
        value not in {None, ""}
        for value in final_values.values()
    )
    assert final_values["supplier_name"] == "А1 България ЕАД"

    assert body["collections"] == {
        "services": [],
        "metering_points": [],
        "meters": [],
        "consumption_items": [],
    }

    quality = body["quality"]
    assert quality["status"] == "accepted"
    assert quality["requires_review"] is False
    warning_codes = {
        warning["code"]
        for warning in quality["warnings"]
    }
    assert "unknown_supplier_profile" not in warning_codes
