from pathlib import Path

import pytest

import scripts.apply_configuration_restore as restore_module
from configuration_revision import configuration_revision
from configuration_snapshot import build_configuration_snapshot


CURRENT_CONFIG = {
    "invoice": {
        "fields": [],
    }
}

RESTORE_CONFIG = {
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

CURRENT_REVISION = configuration_revision(CURRENT_CONFIG)
RESTORE_REVISION = configuration_revision(RESTORE_CONFIG)


class Lock:
    def __init__(self, events):
        self.events = events

    def __enter__(self):
        self.events.append("lock_enter")

    def __exit__(self, exc_type, exc, traceback):
        self.events.append("lock_exit")


def install_snapshot(monkeypatch):
    monkeypatch.setattr(
        restore_module,
        "load_snapshot_file",
        lambda path: build_configuration_snapshot(RESTORE_CONFIG),
    )


def test_restore_orders_lock_backup_recheck_write_and_verify(
    monkeypatch,
    tmp_path,
):
    install_snapshot(monkeypatch)
    events = []
    current = [CURRENT_CONFIG]
    backup_path = tmp_path / "backup.config-snapshot.json"

    monkeypatch.setattr(
        restore_module,
        "configuration_write_lock",
        lambda: Lock(events),
    )

    def load():
        events.append("load")
        return current[0]

    monkeypatch.setattr(restore_module, "load_config", load)

    def backup(**kwargs):
        events.append("backup")
        backup_path.write_text("verified backup\n", encoding="utf-8")
        return {"backup_revision": CURRENT_REVISION}

    monkeypatch.setattr(
        restore_module,
        "create_verified_pre_restore_backup",
        backup,
    )

    def write(config):
        events.append("write")
        current[0] = config

    monkeypatch.setattr(restore_module, "_save_config_unlocked", write)

    result = restore_module.apply_configuration_restore(
        snapshot_path=tmp_path / "restore.config-snapshot.json",
        backup_output=backup_path,
        expected_current_revision=CURRENT_REVISION,
        confirmation="RESTORE",
    )

    assert events == [
        "lock_enter",
        "load",
        "backup",
        "load",
        "write",
        "load",
        "lock_exit",
    ]
    assert result["restore_applied"] is True
    assert result["restored_revision"] == RESTORE_REVISION
    assert result["backup_revision"] == CURRENT_REVISION
    assert result["configuration_write"] == "PERFORMED"


def test_stale_revision_before_backup_blocks_every_write(monkeypatch, tmp_path):
    install_snapshot(monkeypatch)
    events = []
    monkeypatch.setattr(
        restore_module,
        "configuration_write_lock",
        lambda: Lock(events),
    )
    monkeypatch.setattr(restore_module, "load_config", lambda: CURRENT_CONFIG)
    monkeypatch.setattr(
        restore_module,
        "create_verified_pre_restore_backup",
        lambda **kwargs: pytest.fail("backup must not be created"),
    )
    monkeypatch.setattr(
        restore_module,
        "_save_config_unlocked",
        lambda config: pytest.fail("configuration must not be written"),
    )

    with pytest.raises(
        restore_module.AtomicConfigurationRestoreError,
        match="changed before backup",
    ):
        restore_module.apply_configuration_restore(
            snapshot_path=tmp_path / "restore.config-snapshot.json",
            backup_output=tmp_path / "backup.config-snapshot.json",
            expected_current_revision="0" * 64,
            confirmation="RESTORE",
        )

    assert events == ["lock_enter", "lock_exit"]




def test_snapshot_change_after_initial_validation_blocks_write(
    monkeypatch,
    tmp_path,
):
    install_snapshot(monkeypatch)
    backup_path = tmp_path / "backup.config-snapshot.json"

    monkeypatch.setattr(
        restore_module,
        "configuration_write_lock",
        lambda: Lock([]),
    )
    monkeypatch.setattr(
        restore_module,
        "load_config",
        lambda: CURRENT_CONFIG,
    )

    def backup(**kwargs):
        backup_path.write_text(
            "verified backup\n",
            encoding="utf-8",
        )
        return {
            "snapshot_revision": "c" * 64,
            "backup_revision": CURRENT_REVISION,
        }

    monkeypatch.setattr(
        restore_module,
        "create_verified_pre_restore_backup",
        backup,
    )
    monkeypatch.setattr(
        restore_module,
        "_save_config_unlocked",
        lambda config: pytest.fail(
            "changed snapshot must not be written"
        ),
    )

    with pytest.raises(
        restore_module.AtomicConfigurationRestoreError,
        match="snapshot changed",
    ):
        restore_module.apply_configuration_restore(
            snapshot_path=(
                tmp_path / "restore.config-snapshot.json"
            ),
            backup_output=backup_path,
            expected_current_revision=CURRENT_REVISION,
            confirmation="RESTORE",
        )

    assert not backup_path.exists()


def test_revision_change_after_backup_removes_backup_and_blocks_write(
    monkeypatch,
    tmp_path,
):
    install_snapshot(monkeypatch)
    backup_path = tmp_path / "backup.config-snapshot.json"
    loads = iter([CURRENT_CONFIG, RESTORE_CONFIG])

    monkeypatch.setattr(
        restore_module,
        "configuration_write_lock",
        lambda: Lock([]),
    )
    monkeypatch.setattr(restore_module, "load_config", lambda: next(loads))

    def backup(**kwargs):
        backup_path.write_text("verified backup\n", encoding="utf-8")
        return {"backup_revision": CURRENT_REVISION}

    monkeypatch.setattr(
        restore_module,
        "create_verified_pre_restore_backup",
        backup,
    )
    monkeypatch.setattr(
        restore_module,
        "_save_config_unlocked",
        lambda config: pytest.fail("configuration must not be written"),
    )

    with pytest.raises(
        restore_module.AtomicConfigurationRestoreError,
        match="immediately before write",
    ):
        restore_module.apply_configuration_restore(
            snapshot_path=tmp_path / "restore.config-snapshot.json",
            backup_output=backup_path,
            expected_current_revision=CURRENT_REVISION,
            confirmation="RESTORE",
        )

    assert not backup_path.exists()


def test_atomic_write_failure_keeps_verified_backup(monkeypatch, tmp_path):
    install_snapshot(monkeypatch)
    backup_path = tmp_path / "backup.config-snapshot.json"
    monkeypatch.setattr(
        restore_module,
        "configuration_write_lock",
        lambda: Lock([]),
    )
    monkeypatch.setattr(restore_module, "load_config", lambda: CURRENT_CONFIG)

    def backup(**kwargs):
        backup_path.write_text("verified backup\n", encoding="utf-8")
        return {"backup_revision": CURRENT_REVISION}

    monkeypatch.setattr(
        restore_module,
        "create_verified_pre_restore_backup",
        backup,
    )
    monkeypatch.setattr(
        restore_module,
        "_save_config_unlocked",
        lambda config: (_ for _ in ()).throw(OSError("simulated write failure")),
    )

    with pytest.raises(OSError, match="simulated write failure"):
        restore_module.apply_configuration_restore(
            snapshot_path=tmp_path / "restore.config-snapshot.json",
            backup_output=backup_path,
            expected_current_revision=CURRENT_REVISION,
            confirmation="RESTORE",
        )

    assert backup_path.read_text(encoding="utf-8") == "verified backup\n"


def test_post_write_verification_failure_rolls_back(monkeypatch, tmp_path):
    install_snapshot(monkeypatch)
    backup_path = tmp_path / "backup.config-snapshot.json"
    current = [CURRENT_CONFIG]
    writes = []

    monkeypatch.setattr(
        restore_module,
        "configuration_write_lock",
        lambda: Lock([]),
    )
    monkeypatch.setattr(restore_module, "load_config", lambda: current[0])

    def backup(**kwargs):
        backup_path.write_text("backup\n", encoding="utf-8")
        return {"backup_revision": CURRENT_REVISION}

    monkeypatch.setattr(
        restore_module,
        "create_verified_pre_restore_backup",
        backup,
    )

    def write(config):
        writes.append(config)
        if len(writes) == 1:
            current[0] = {"invoice": {"fields": [], "collections": {}}}
        else:
            current[0] = config

    monkeypatch.setattr(restore_module, "_save_config_unlocked", write)
    monkeypatch.setattr(
        restore_module,
        "load_snapshot_file",
        lambda path: (
            build_configuration_snapshot(CURRENT_CONFIG)
            if path == backup_path
            else build_configuration_snapshot(RESTORE_CONFIG)
        ),
    )

    with pytest.raises(
        restore_module.AtomicConfigurationRestoreError,
        match="original configuration restored",
    ):
        restore_module.apply_configuration_restore(
            snapshot_path=tmp_path / "restore.config-snapshot.json",
            backup_output=backup_path,
            expected_current_revision=CURRENT_REVISION,
            confirmation="RESTORE",
        )

    assert writes == [RESTORE_CONFIG, CURRENT_CONFIG]
    assert current[0] == CURRENT_CONFIG


def test_restore_cli_requires_explicit_safety_inputs():
    content = Path(restore_module.__file__).read_text(encoding="utf-8")

    assert '"--backup-output"' in content
    assert '"--expected-current-revision"' in content
    assert '"--confirm"' in content
    assert "configuration_write: PERFORMED" in content
