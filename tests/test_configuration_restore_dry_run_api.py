from copy import deepcopy

from fastapi.testclient import TestClient

from api import app
from config_store import load_config
from configuration_revision import configuration_revision
from configuration_snapshot import build_configuration_snapshot


CLIENT = TestClient(app)
ENDPOINT = "/api/v1/config/restore/dry-run"


def test_restore_dry_run_accepts_unchanged_snapshot():
    snapshot = build_configuration_snapshot(load_config())

    response = CLIENT.post(ENDPOINT, json=snapshot)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "valid": True,
        "snapshot_revision": snapshot["revision"],
        "current_revision": snapshot["revision"],
        "changes_detected": False,
        "document_types": sorted(snapshot["configuration"]),
    }


def test_restore_dry_run_reports_changed_snapshot():
    snapshot = build_configuration_snapshot(load_config())
    candidate = deepcopy(snapshot["configuration"])
    candidate["invoice"]["default_profile"] = None
    changed_snapshot = build_configuration_snapshot(candidate)

    response = CLIENT.post(ENDPOINT, json=changed_snapshot)

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["changes_detected"] is True
    assert body["snapshot_revision"] == configuration_revision(candidate)
    assert body["current_revision"] == snapshot["revision"]


def test_restore_dry_run_rejects_tampered_snapshot():
    snapshot = build_configuration_snapshot(load_config())
    snapshot["revision"] = "0" * 64

    response = CLIENT.post(ENDPOINT, json=snapshot)

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Configuration snapshot revision does not match its content"
    )


def test_restore_dry_run_is_documented_as_read_only():
    operation = app.openapi()["paths"][ENDPOINT]["post"]

    assert operation["summary"] == (
        "Validate configuration restore candidate"
    )
    assert "read-only" in operation["description"]
    assert "never writes configuration" in operation["description"]
    assert "200" in operation["responses"]
    assert "422" in operation["responses"]
