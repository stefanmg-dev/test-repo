import json
from pathlib import Path

import pytest

import scripts.plan_configuration_restore as plan_module
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


def dry_run_result(*, changes_detected=True):
    return {
        "valid": True,
        "snapshot_revision": "b" * 64,
        "current_revision": "a" * 64,
        "changes_detected": changes_detected,
        "document_types": ["invoice"],
    }


def test_plan_requires_exact_confirmation(monkeypatch, tmp_path):
    monkeypatch.setattr(
        plan_module,
        "validate_restore_dry_run",
        lambda path: pytest.fail("dry-run must not execute"),
    )

    with pytest.raises(
        plan_module.RestoreApplyPlanError,
        match="exactly RESTORE",
    ):
        plan_module.build_restore_apply_plan(
            snapshot_path=tmp_path / "snapshot.json",
            backup_output=tmp_path / "backup.json",
            expected_current_revision="a" * 64,
            confirmation="restore",
        )


def test_plan_rejects_stale_expected_current_revision(monkeypatch, tmp_path):
    monkeypatch.setattr(
        plan_module,
        "validate_restore_dry_run",
        lambda path: dry_run_result(),
    )

    with pytest.raises(
        plan_module.RestoreApplyPlanError,
        match="revision changed",
    ):
        plan_module.build_restore_apply_plan(
            snapshot_path=tmp_path / "snapshot.json",
            backup_output=tmp_path / "backup.json",
            expected_current_revision="c" * 64,
            confirmation="RESTORE",
        )


def test_plan_requires_new_distinct_backup_path(monkeypatch, tmp_path):
    monkeypatch.setattr(
        plan_module,
        "validate_restore_dry_run",
        lambda path: dry_run_result(),
    )
    snapshot = tmp_path / "snapshot.json"

    with pytest.raises(
        plan_module.RestoreApplyPlanError,
        match="must differ",
    ):
        plan_module.build_restore_apply_plan(
            snapshot_path=snapshot,
            backup_output=snapshot,
            expected_current_revision="a" * 64,
            confirmation="RESTORE",
        )

    backup = tmp_path / "existing-backup.json"
    backup.write_text("trusted\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="already exists"):
        plan_module.build_restore_apply_plan(
            snapshot_path=snapshot,
            backup_output=backup,
            expected_current_revision="a" * 64,
            confirmation="RESTORE",
        )

    assert backup.read_text(encoding="utf-8") == "trusted\n"


def test_valid_plan_is_read_only(monkeypatch, tmp_path):
    monkeypatch.setattr(
        plan_module,
        "validate_restore_dry_run",
        lambda path: dry_run_result(),
    )
    snapshot = tmp_path / "snapshot.json"
    backup = tmp_path / "backup.config-snapshot.json"

    plan = plan_module.build_restore_apply_plan(
        snapshot_path=snapshot,
        backup_output=backup,
        expected_current_revision="a" * 64,
        confirmation="RESTORE",
    )

    assert plan["plan_valid"] is True
    assert plan["backup_required"] is True
    assert plan["configuration_write"] == "NOT_PERFORMED"
    assert plan["current_revision"] == "a" * 64
    assert plan["snapshot_revision"] == "b" * 64
    assert not backup.exists()


def test_plan_cli_has_no_apply_or_write_path():
    content = Path(plan_module.__file__).read_text(encoding="utf-8")

    assert "save_config" not in content
    assert "os.replace" not in content
    assert "--apply" not in content
    assert "configuration_write: NOT_PERFORMED" in content
    assert 'RESTORE_CONFIRMATION = "RESTORE"' in content
