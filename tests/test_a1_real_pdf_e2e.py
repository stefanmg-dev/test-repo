import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app
from config_store import load_config


PDF_CASES = (
    ("A1_REAL_PDF_PATH", "manual-a1-regression.pdf"),
    ("A1_SEPTEMBER_REAL_PDF_PATH", "manual-a1-september-regression.pdf"),
)


def get_real_pdf_path(environment_name: str) -> Path:
    configured_path = os.getenv(environment_name)
    if not configured_path:
        pytest.skip(f"{environment_name} is not configured")

    pdf_path = Path(configured_path).expanduser()
    if not pdf_path.is_file():
        pytest.fail("Configured real A1 PDF was not found")
    return pdf_path


def assert_a1_response_contract(body):
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


def run_real_a1_pdf_case(monkeypatch, environment_name, upload_name):
    pdf_path = get_real_pdf_path(environment_name)
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
                    upload_name,
                    pdf_file,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    assert_a1_response_contract(response.json())


def test_real_a1_pdf_end_to_end(monkeypatch):
    run_real_a1_pdf_case(
        monkeypatch,
        "A1_REAL_PDF_PATH",
        "manual-a1-regression.pdf",
    )


def test_real_a1_september_pdf_end_to_end(monkeypatch):
    run_real_a1_pdf_case(
        monkeypatch,
        "A1_SEPTEMBER_REAL_PDF_PATH",
        "manual-a1-september-regression.pdf",
    )
