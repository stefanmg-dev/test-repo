from pathlib import Path

from fastapi.testclient import TestClient

from api import app
from config_store import load_config
from configuration_snapshot import build_configuration_snapshot
import routes_config_v1
from scripts.apply_configuration_restore import (
    AtomicConfigurationRestoreError,
)


CLIENT = TestClient(app)
ENDPOINT = "/api/v1/config/restore"


def restore_request():
    snapshot = build_configuration_snapshot(load_config())
    return {
        "snapshot": snapshot,
        "expected_current_revision": snapshot["revision"],
        "confirmation": "RESTORE",
    }


def test_guarded_restore_uses_atomic_primitive_and_controlled_backup(
    monkeypatch,
):
    observed = {}

    def fake_restore(**kwargs):
        observed.update(kwargs)
        assert kwargs["snapshot_path"].exists()
        assert kwargs["backup_output"].parent.name == "restore_backups"
        assert kwargs["backup_output"].name.startswith("pre-restore-")
        assert kwargs["backup_output"].name.endswith(
            ".config-snapshot.json"
        )
        return {
            "restore_applied": True,
            "previous_revision": kwargs["expected_current_revision"],
            "restored_revision": "1" * 64,
            "backup_revision": kwargs["expected_current_revision"],
            "configuration_write": "PERFORMED",
        }

    monkeypatch.setattr(
        routes_config_v1,
        "apply_configuration_restore",
        fake_restore,
    )

    response = CLIENT.post(ENDPOINT, json=restore_request())

    assert response.status_code == 200
    body = response.json()
    assert body["restore_applied"] is True
    assert body["restored_revision"] == "1" * 64
    assert body["backup_identifier"].startswith("pre-restore-")
    assert "/" not in body["backup_identifier"]
    assert observed["confirmation"] == "RESTORE"
    assert not observed["snapshot_path"].exists()


def test_guarded_restore_requires_exact_confirmation():
    request = restore_request()
    request["confirmation"] = "restore"

    response = CLIENT.post(ENDPOINT, json=request)

    assert response.status_code == 422


def test_guarded_restore_maps_revision_conflict(monkeypatch):
    def fail_restore(**kwargs):
        raise AtomicConfigurationRestoreError(
            "Current configuration revision changed before backup"
        )

    monkeypatch.setattr(
        routes_config_v1,
        "apply_configuration_restore",
        fail_restore,
    )

    response = CLIENT.post(ENDPOINT, json=restore_request())

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Current configuration revision changed before backup"
    )


def test_guarded_restore_openapi_contract():
    operation = app.openapi()["paths"][ENDPOINT]["post"]

    assert operation["summary"] == "Apply guarded configuration restore"
    assert "config:write" in operation["description"]
    assert "verified pre-restore backup" in operation["description"]
    assert "200" in operation["responses"]
    assert "422" in operation["responses"]
