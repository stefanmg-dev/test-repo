import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import routes_extract
from api import app


PDF_PATH_ENV = "TOPLOFIKACIA_REAL_PDF_PATH"


def get_real_pdf_path() -> Path:
    configured_path = os.getenv(PDF_PATH_ENV)

    if not configured_path:
        pytest.skip(
            f"{PDF_PATH_ENV} is not configured"
        )

    pdf_path = Path(configured_path).expanduser()

    if not pdf_path.is_file():
        pytest.fail(
            f"Real Toplofikacia PDF was not found: {pdf_path}"
        )

    return pdf_path


def test_real_toplofikacia_pdf_end_to_end(
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

    assert body["document_type"] == "invoice"
    assert body["profile"] == "heating_toplofikacia_sofia"
    import json

    Path(
        "/tmp/toplofikacia_collection_diagnostic.json"
    ).write_text(
        json.dumps(
            {
                "processing_status": body["processing_status"],
                "collection_validation": (
                    body["collection_validation"]
                ),
                "services": body["collections"]["services"],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    assert body["processing_status"] == "accepted"

    assert body["validation"] == {
        "valid": True,
        "errors": {},
    }
    assert body["collection_validation"] == {
        "valid": True,
        "errors": {},
    }

    final_values = body["final_values"]

    expected_scalar_fields = {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "customer_name",
        "customer_address",
        "due_date",
        "total_amount",
        "business_partner_number",
        "contract_account_number",
        "installation_number",
    }

    assert set(final_values) == expected_scalar_fields

    for field_name in expected_scalar_fields:
        assert final_values[field_name] not in {
            None,
            "",
        }

    assert final_values["supplier_name"] == (
        "Топлофикация София ЕАД"
    )

    collections = body["collections"]

    assert collections["services"] == [
        {
            "description": (
                "Топлинна енергия за подгряване на вода"
            ),
            "unit": "МВтч",
            "quantity": "0.143953",
            "unit_price": "73.30",
            "amount": "10.55",
        },
        {
            "description": (
                "Топлинна енергия за отопление на имот"
            ),
            "unit": "МВтч",
            "quantity": "0.000000",
            "unit_price": "73.30",
            "amount": "0.00",
        },
        {
            "description": (
                "Дялово разпределение на топлинна енергия "
                "(1/12 част)"
            ),
            "unit": "бр",
            "quantity": "1",
            "unit_price": "2.05",
            "amount": "2.05",
        },
    ]

    assert collections["metering_points"] == []
    assert collections["meters"] == []
    assert collections["consumption_items"] == []

    warning_codes = {
        warning["code"]
        for warning in body["quality"]["warnings"]
    }
    assert "unknown_supplier_profile" not in warning_codes
