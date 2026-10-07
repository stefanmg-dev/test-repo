from fastapi.testclient import TestClient

import routes_config_v1
from api import app
from configuration_revision import (
    configuration_etag,
    configuration_revision,
)


CONFIG = {
    "invoice": {
        "fields": [],
    }
}


def test_configuration_list_returns_revision_and_etag(
    monkeypatch,
):
    monkeypatch.setattr(
        routes_config_v1,
        "load_config",
        lambda: CONFIG,
    )

    response = TestClient(app).get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 200

    expected_revision = configuration_revision(
        CONFIG
    )

    assert response.json()["revision"] == (
        expected_revision
    )
    assert response.headers["ETag"] == (
        configuration_etag(expected_revision)
    )


def test_configuration_revision_schema_is_documented():
    schemas = app.openapi()["components"]["schemas"]
    revision = schemas["ConfigResponse"][
        "properties"
    ]["revision"]

    assert revision["description"]
    assert revision["minLength"] == 64
    assert revision["maxLength"] == 64
    assert revision["pattern"] == (
        "^[0-9a-f]{64}$"
    )
    assert revision["examples"] == [
        "0" * 64
    ]
