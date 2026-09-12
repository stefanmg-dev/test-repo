import routes_config_v1
from fastapi.testclient import TestClient

from api import app


READY_CONFIG = {
    "invoice": {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": "([0-9]+)",
                "occurrence": "first",
                "validation": [],
            },
            {
                "name": "total_amount",
                "type": "regex",
                "rule": "([0-9]+\\.[0-9]+)",
                "occurrence": "last",
                "validation": [],
            },
        ]
    },
    "contract": {
        "fields": []
    },
}


def test_document_types_response_contains_metadata(
    monkeypatch
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: READY_CONFIG,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 200

    response_body = response.json()

    assert response_body["document_types"] == (
        READY_CONFIG
    )

    assert response_body[
        "document_type_metadata"
    ] == {
        "invoice": {
            "status": "ready",
            "ready": True,
            "field_count": 2,
        },
        "contract": {
            "status": "draft",
            "ready": False,
            "field_count": 0,
        },
    }


def test_metadata_matches_every_document_type(
    monkeypatch
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: READY_CONFIG,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 200

    response_body = response.json()

    document_type_names = set(
        response_body["document_types"]
    )

    metadata_names = set(
        response_body["document_type_metadata"]
    )

    assert metadata_names == document_type_names


def test_ready_metadata_field_count_is_correct(
    monkeypatch
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: READY_CONFIG,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/config/document-types"
    )

    metadata = response.json()[
        "document_type_metadata"
    ]

    assert metadata["invoice"]["field_count"] == 2
    assert metadata["invoice"]["ready"] is True
    assert metadata["invoice"]["status"] == "ready"


def test_empty_document_type_metadata_is_draft(
    monkeypatch
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: READY_CONFIG,
    )

    client = TestClient(app)

    response = client.get(
        "/api/v1/config/document-types"
    )

    metadata = response.json()[
        "document_type_metadata"
    ]

    assert metadata["contract"] == {
        "status": "draft",
        "ready": False,
        "field_count": 0,
    }