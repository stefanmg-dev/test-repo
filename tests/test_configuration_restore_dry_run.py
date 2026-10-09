import json
from pathlib import Path

import pytest

import scripts.validate_configuration_restore as restore_module
from configuration_snapshot import build_configuration_snapshot


CURRENT_CONFIG = {
    "invoice": {
        "fields": [],
    }
}

CHANGED_CONFIG = {
    "invoice": {
        "fields": [
            {
                "name": "supplier_name",
                "type": "constant",
                "value": "synthetic",
            }
        ],
    }
}


def write_snapshot(path, config):
    path.write_text(
        json.dumps(build_configuration_snapshot(config), indent=2) + "\n",
        encoding="utf-8",
    )


def test_dry_run_accepts_valid_unchanged_snapshot(monkeypatch, tmp_path):
    snapshot_path = tmp_path / "current.config-snapshot.json"
    write_snapshot(snapshot_path, CURRENT_CONFIG)
    monkeypatch.setattr(restore_module, "load_config", lambda: CURRENT_CONFIG)

    result = restore_module.validate_restore_dry_run(snapshot_path)

    assert result["valid"] is True
    assert result["changes_detected"] is False
    assert result["snapshot_revision"] == result["current_revision"]
    assert result["document_types"] == ["invoice"]


def test_dry_run_reports_changed_snapshot(monkeypatch, tmp_path):
    snapshot_path = tmp_path / "changed.config-snapshot.json"
    write_snapshot(snapshot_path, CHANGED_CONFIG)
    monkeypatch.setattr(restore_module, "load_config", lambda: CURRENT_CONFIG)

    result = restore_module.validate_restore_dry_run(snapshot_path)

    assert result["valid"] is True
    assert result["changes_detected"] is True
    assert result["snapshot_revision"] != result["current_revision"]


def test_dry_run_rejects_invalid_json(tmp_path):
    snapshot_path = tmp_path / "broken.config-snapshot.json"
    snapshot_path.write_text("{broken", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        restore_module.validate_restore_dry_run(snapshot_path)


def test_dry_run_rejects_tampered_snapshot(monkeypatch, tmp_path):
    snapshot = build_configuration_snapshot(CHANGED_CONFIG)
    snapshot["revision"] = "0" * 64
    snapshot_path = tmp_path / "tampered.config-snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    monkeypatch.setattr(restore_module, "load_config", lambda: CURRENT_CONFIG)

    with pytest.raises(ValueError, match="revision does not match"):
        restore_module.validate_restore_dry_run(snapshot_path)


def test_dry_run_requires_existing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="was not found"):
        restore_module.validate_restore_dry_run(
            tmp_path / "missing.config-snapshot.json"
        )


def test_restore_validator_has_no_configuration_write_path():
    content = Path(restore_module.__file__).read_text(encoding="utf-8")

    assert "save_config" not in content
    assert "os.replace" not in content
    assert "--apply" not in content
    assert "configuration_write: NOT_PERFORMED" in content
