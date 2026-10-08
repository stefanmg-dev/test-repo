import json

import pytest
from fastapi.testclient import TestClient

import config_store
from api import app
from configuration_revision import (
    configuration_etag,
    configuration_revision,
)


INITIAL_CONFIG = {
    "invoice": {
        "fields": [],
    }
}


@pytest.fixture
def guarded_client(tmp_path, monkeypatch):
    config_path = tmp_path / "document_types.json"
    config_path.write_text(
        json.dumps(INITIAL_CONFIG, indent=2) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config_store, "CONFIG_PATH", config_path)

    with TestClient(app) as client:
        yield client, config_path


def read_config(path):
    return json.loads(path.read_text(encoding="utf-8"))


def current_etag():
    return configuration_etag(
        configuration_revision(INITIAL_CONFIG)
    )


def test_stale_if_match_blocks_main_router_without_write(guarded_client):
    client, config_path = guarded_client

    response = client.post(
        "/api/v1/config/document-types",
        headers={"If-Match": '"stale"'},
        json={"document_type": "contract"},
    )

    assert response.status_code == 412
    assert response.json() == {
        "detail": (
            "Configuration revision is stale. "
            "Reload the configuration and retry."
        )
    }
    assert response.headers["ETag"] == current_etag()
    assert read_config(config_path) == INITIAL_CONFIG


def test_stale_if_match_blocks_collection_router_without_write(
    guarded_client,
):
    client, config_path = guarded_client

    response = client.post(
        "/api/v1/config/document-types/invoice/collections/services",
        headers={"If-Match": 'W/"stale"'},
        json={
            "collection": {
                "cardinality": "zero_or_more",
                "fields": [],
            }
        },
    )

    assert response.status_code == 412
    assert response.headers["ETag"] == current_etag()
    assert read_config(config_path) == INITIAL_CONFIG


def test_current_if_match_allows_main_router_mutation(guarded_client):
    client, config_path = guarded_client

    response = client.post(
        "/api/v1/config/document-types",
        headers={"If-Match": current_etag()},
        json={"document_type": "contract"},
    )

    assert response.status_code == 201
    assert read_config(config_path)["contract"] == {"fields": []}


def test_missing_if_match_remains_backward_compatible(guarded_client):
    client, config_path = guarded_client

    response = client.post(
        "/api/v1/config/document-types",
        json={"document_type": "contract"},
    )

    assert response.status_code == 201
    assert read_config(config_path)["contract"] == {"fields": []}


def test_all_configuration_mutations_document_optional_if_match():
    paths = app.openapi()["paths"]
    checked = 0

    for route, operations in paths.items():
        if not route.startswith("/api/v1/config/"):
            continue
        for method in ("post", "put", "delete"):
            operation = operations.get(method)
            if operation is None:
                continue
            parameters = {
                (item["name"], item["in"]): item
                for item in operation.get("parameters", [])
            }
            parameter = parameters[("If-Match", "header")]
            assert parameter["required"] is False
            assert parameter["description"]
            checked += 1

    assert checked == 31
