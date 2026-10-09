from pathlib import Path

import pytest

import scripts.create_configuration_restore_backup as backup_module


PLAN = {
    "plan_valid": True,
    "snapshot_path": "/tmp/restore.config-snapshot.json",
    "snapshot_revision": "b" * 64,
    "current_revision": "a" * 64,
    "changes_detected": True,
    "backup_output": "/tmp/backup.config-snapshot.json",
    "backup_required": True,
    "configuration_write": "NOT_PERFORMED",
}


def test_backup_is_created_only_after_valid_plan(monkeypatch, tmp_path):
    backup_path = tmp_path / "backup.config-snapshot.json"
    plan = {**PLAN, "backup_output": str(backup_path)}
    calls = []

    monkeypatch.setattr(
        backup_module,
        "build_restore_apply_plan",
        lambda **kwargs: calls.append("plan") or plan,
    )

    def export(path):
        calls.append("backup")
        path.write_text("verified backup\n", encoding="utf-8")
        return {"revision": "a" * 64}

    monkeypatch.setattr(
        backup_module,
        "export_configuration_snapshot",
        export,
    )

    result = backup_module.create_verified_pre_restore_backup(
        snapshot_path=tmp_path / "restore.config-snapshot.json",
        backup_output=backup_path,
        expected_current_revision="a" * 64,
        confirmation="RESTORE",
    )

    assert calls == ["plan", "backup"]
    assert result["backup_created"] is True
    assert result["backup_revision"] == "a" * 64
    assert result["configuration_write"] == "NOT_PERFORMED"
    assert backup_path.read_text(encoding="utf-8") == "verified backup\n"


def test_plan_failure_prevents_backup_creation(monkeypatch, tmp_path):
    backup_path = tmp_path / "backup.config-snapshot.json"

    def fail_plan(**kwargs):
        raise ValueError("invalid restore plan")

    monkeypatch.setattr(
        backup_module,
        "build_restore_apply_plan",
        fail_plan,
    )
    monkeypatch.setattr(
        backup_module,
        "export_configuration_snapshot",
        lambda path: pytest.fail("backup must not be created"),
    )

    with pytest.raises(ValueError, match="invalid restore plan"):
        backup_module.create_verified_pre_restore_backup(
            snapshot_path=tmp_path / "restore.config-snapshot.json",
            backup_output=backup_path,
            expected_current_revision="a" * 64,
            confirmation="RESTORE",
        )

    assert not backup_path.exists()


def test_revision_mismatch_removes_created_backup(monkeypatch, tmp_path):
    backup_path = tmp_path / "backup.config-snapshot.json"
    plan = {**PLAN, "backup_output": str(backup_path)}

    monkeypatch.setattr(
        backup_module,
        "build_restore_apply_plan",
        lambda **kwargs: plan,
    )

    def export(path):
        path.write_text("mismatched backup\n", encoding="utf-8")
        return {"revision": "c" * 64}

    monkeypatch.setattr(
        backup_module,
        "export_configuration_snapshot",
        export,
    )

    with pytest.raises(RuntimeError, match="does not match"):
        backup_module.create_verified_pre_restore_backup(
            snapshot_path=tmp_path / "restore.config-snapshot.json",
            backup_output=backup_path,
            expected_current_revision="a" * 64,
            confirmation="RESTORE",
        )

    assert not backup_path.exists()


def test_backup_orchestrator_has_no_restore_write_path():
    content = Path(backup_module.__file__).read_text(encoding="utf-8")

    assert "save_config" not in content
    assert "os.replace" not in content
    assert "--apply" not in content
    assert "configuration_write: NOT_PERFORMED" in content
