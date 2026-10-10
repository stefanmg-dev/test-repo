from fastapi.testclient import TestClient

from api import app
from config_store import load_config
from configuration_revision import configuration_etag
from configuration_snapshot import build_configuration_snapshot


def test_configuration_snapshot_endpoint_returns_current_snapshot():
    response = TestClient(app).get("/api/v1/config/snapshot")

    assert response.status_code == 200
    expected = build_configuration_snapshot(load_config())
    assert response.json() == expected
    assert response.headers["etag"] == configuration_etag(
        expected["revision"]
    )


def test_configuration_snapshot_endpoint_is_documented_in_openapi():
    operation = app.openapi()["paths"][
        "/api/v1/config/snapshot"
    ]["get"]

    assert operation["summary"] == "Export configuration snapshot"
    assert "config:read" in operation["description"]
    assert "200" in operation["responses"]
