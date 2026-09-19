import json

import pytest
from fastapi.testclient import TestClient

import config_store
from api import app


INITIAL_CONFIG = {
    "invoice": {
        "fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": (
                    "Фактура\\s*№\\s*"
                    "([0-9]{8,15})"
                ),
                "occurrence": "first",
                "validation": [
                    {
                        "type": "required",
                        "message": (
                            "Invoice number is required"
                        )
                    }
                ]
            }
        ]
    }
}


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    temporary_config_path = (
        tmp_path / "document_types.json"
    )

    temporary_config_path.write_text(
        json.dumps(
            INITIAL_CONFIG,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        config_store,
        "CONFIG_PATH",
        temporary_config_path
    )

    return temporary_config_path


@pytest.fixture
def client(isolated_config):
    with TestClient(app) as test_client:
        yield test_client


def read_temporary_config(path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def test_get_document_types(
    client,
    isolated_config
):
    response = client.get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 200

    response_body = response.json()

    assert "invoice" in response_body["document_types"]

    stored_config = read_temporary_config(
        isolated_config
    )

    assert stored_config == INITIAL_CONFIG


def test_document_type_crud_flow(
    client,
    isolated_config
):
    create_response = client.post(
        "/api/v1/config/document-types",
        json={
            "document_type": "contract"
        }
    )

    assert create_response.status_code == 201

    config_after_create = read_temporary_config(
        isolated_config
    )

    assert config_after_create["contract"] == {
        "fields": []
    }

    get_response = client.get(
        "/api/v1/config/document-types/contract"
    )

    assert get_response.status_code == 200
    assert get_response.json() == {
        "fields": []
    }

    rename_response = client.put(
        "/api/v1/config/document-types/"
        "contract/rename",
        json={
            "new_document_type": "agreement"
        }
    )

    assert rename_response.status_code == 200

    config_after_rename = read_temporary_config(
        isolated_config
    )

    assert "contract" not in config_after_rename
    assert "agreement" in config_after_rename

    delete_response = client.delete(
        "/api/v1/config/document-types/agreement"
    )

    assert delete_response.status_code == 204

    final_config = read_temporary_config(
        isolated_config
    )

    assert "agreement" not in final_config
    assert "invoice" in final_config


def test_field_crud_flow(
    client,
    isolated_config
):
    add_response = client.post(
        "/api/v1/config/document-types/"
        "invoice/fields",
        json={
            "field": {
                "name": "total_amount",
                "type": "regex",
                "rule": (
                    "Обща стойност\\s*"
                    "([0-9]+\\.[0-9]+)"
                ),
                "occurrence": "last",
                "validation": [
                    {
                        "type": "required",
                        "message": (
                            "Total amount is required"
                        )
                    },
                    {
                        "type": "decimal",
                        "minimum": "0.01",
                        "message": (
                            "Total amount must be positive"
                        )
                    }
                ]
            }
        }
    )

    assert add_response.status_code == 201

    config_after_add = read_temporary_config(
        isolated_config
    )

    added_field = next(
        field
        for field in config_after_add[
            "invoice"
        ]["fields"]
        if field["name"] == "total_amount"
    )

    assert added_field["type"] == "regex"
    assert added_field["occurrence"] == "last"

    update_response = client.put(
        "/api/v1/config/document-types/"
        "invoice/fields/total_amount",
        json={
            "field": {
                "name": "amount_due",
                "type": "regex",
                "rule": (
                    "Обща стойност за плащане\\s*"
                    "([0-9]+\\.[0-9]+)"
                ),
                "occurrence": "last",
                "validation": [
                    {
                        "type": "required",
                        "message": (
                            "Amount due is required"
                        )
                    }
                ]
            }
        }
    )

    assert update_response.status_code == 200

    config_after_update = read_temporary_config(
        isolated_config
    )

    field_names = [
        field["name"]
        for field in config_after_update[
            "invoice"
        ]["fields"]
    ]

    assert "total_amount" not in field_names
    assert "amount_due" in field_names

    delete_response = client.delete(
        "/api/v1/config/document-types/"
        "invoice/fields/amount_due"
    )

    assert delete_response.status_code == 200

    config_after_delete = read_temporary_config(
        isolated_config
    )

    remaining_field_names = [
        field["name"]
        for field in config_after_delete[
            "invoice"
        ]["fields"]
    ]

    assert remaining_field_names == [
        "invoice_number"
    ]


def test_rejects_duplicate_document_type(
    client
):
    response = client.post(
        "/api/v1/config/document-types",
        json={
            "document_type": "invoice"
        }
    )

    assert response.status_code == 409

    assert response.json()["detail"] == (
        "Document type 'invoice' already exists"
    )


def test_rejects_invalid_field_payload(
    client
):
    response = client.post(
        "/api/v1/config/document-types/"
        "invoice/fields",
        json={
            "field": {
                "name": "broken_field",
                "type": "invalid_type"
            }
        }
    )

    assert response.status_code == 422


def test_collection_crud_flow(
    client,
    isolated_config,
):
    collection_payload = {
        "collection": {
            "cardinality": "zero_or_more",
            "start_pattern": r"^Електромер\s*№",
            "fields": [],
        }
    }

    add_response = client.post(
        "/api/v1/config/document-types/"
        "invoice/collections/meters",
        json=collection_payload,
    )
    assert add_response.status_code == 201

    config_after_add = read_temporary_config(
        isolated_config
    )
    assert config_after_add["invoice"]["collections"][
        "meters"
    ] == collection_payload["collection"]

    updated_payload = {
        "collection": {
            "cardinality": "one_or_more",
            "start_pattern": r"^Фабричен номер",
            "fields": [],
        }
    }
    update_response = client.put(
        "/api/v1/config/document-types/"
        "invoice/collections/meters",
        json=updated_payload,
    )
    assert update_response.status_code == 200

    config_after_update = read_temporary_config(
        isolated_config
    )
    assert config_after_update["invoice"]["collections"][
        "meters"
    ] == updated_payload["collection"]

    delete_response = client.delete(
        "/api/v1/config/document-types/"
        "invoice/collections/meters"
    )
    assert delete_response.status_code == 200

    config_after_delete = read_temporary_config(
        isolated_config
    )
    assert "collections" not in config_after_delete["invoice"]


def test_rejects_duplicate_collection(client):
    payload = {
        "collection": {
            "cardinality": "zero_or_more",
            "fields": [],
        }
    }
    first_response = client.post(
        "/api/v1/config/document-types/"
        "invoice/collections/services",
        json=payload,
    )
    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/api/v1/config/document-types/"
        "invoice/collections/services",
        json=payload,
    )
    assert duplicate_response.status_code == 409


def test_collection_update_and_delete_require_existing_collection(
    client,
):
    payload = {
        "collection": {
            "cardinality": "zero_or_more",
            "fields": [],
        }
    }
    update_response = client.put(
        "/api/v1/config/document-types/"
        "invoice/collections/missing",
        json=payload,
    )
    assert update_response.status_code == 404

    delete_response = client.delete(
        "/api/v1/config/document-types/"
        "invoice/collections/missing"
    )
    assert delete_response.status_code == 404


def test_rejects_invalid_collection_payload(client):
    response = client.post(
        "/api/v1/config/document-types/"
        "invoice/collections/meters",
        json={
            "collection": {
                "cardinality": "many",
                "fields": [],
            }
        },
    )
    assert response.status_code == 422
