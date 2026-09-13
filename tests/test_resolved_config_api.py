from fastapi.testclient import TestClient

import routes_config_v1
from api import app


PROFILE_CONFIG = {
    "invoice": {
        "default_profile": "telecom_a1",
        "common_fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": "([0-9]+)",
            },
            {
                "name": "total_amount",
                "type": "regex",
                "rule": "([0-9]+\\.[0-9]+)",
            },
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "contract_number",
                        "type": "regex",
                        "rule": "([МM][0-9]+)",
                    }
                ]
            }
        },
    }
}


def test_config_api_returns_resolved_document_types(
    monkeypatch,
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: PROFILE_CONFIG,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"

    assert [
        field["name"]
        for field in body["document_types"]["invoice"][
            "common_fields"
        ]
    ] == [
        "invoice_number",
        "total_amount",
    ]

    assert body["resolved_document_types"] == {
        "invoice": {
            "profile": "telecom_a1",
            "fields": [
                {
                    "name": "invoice_number",
                    "type": "regex",
                    "rule": "([0-9]+)",
                    "validation": [],
                },
                {
                    "name": "total_amount",
                    "type": "regex",
                    "rule": "([0-9]+\\.[0-9]+)",
                    "validation": [],
                },
                {
                    "name": "contract_number",
                    "type": "regex",
                    "rule": "([МM][0-9]+)",
                    "validation": [],
                },
            ],
        }
    }

    assert body["document_type_metadata"][
        "invoice"
    ] == {
        "status": "ready",
        "ready": True,
        "field_count": 3,
    }


def test_resolved_configuration_uses_default_profile(
    monkeypatch,
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: PROFILE_CONFIG,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/config/document-types"
    )

    resolved_invoice = response.json()[
        "resolved_document_types"
    ][
        "invoice"
    ]

    assert resolved_invoice["profile"] == (
        "telecom_a1"
    )

    assert [
        field["name"]
        for field in resolved_invoice["fields"]
    ] == [
        "invoice_number",
        "total_amount",
        "contract_number",
    ]