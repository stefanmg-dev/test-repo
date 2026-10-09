#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configuration_revision import configuration_revision
from configuration_snapshot import validate_configuration_snapshot
from config_store import (
    _save_config_unlocked,
    configuration_write_lock,
    load_config,
)
from scripts.create_configuration_restore_backup import (
    create_verified_pre_restore_backup,
)
from scripts.validate_configuration_restore import load_snapshot_file


class AtomicConfigurationRestoreError(RuntimeError):
    pass


def _remove_owned_backup(backup_path: Path) -> None:
    if backup_path.exists():
        backup_path.unlink()


def _restore_verified_backup(
    backup_path: Path,
    expected_revision: str,
) -> None:
    backup_snapshot = load_snapshot_file(backup_path)
    backup_config = validate_configuration_snapshot(backup_snapshot)

    if configuration_revision(backup_config) != expected_revision:
        raise AtomicConfigurationRestoreError(
            "Verified backup revision changed before rollback"
        )

    _save_config_unlocked(backup_config)

    restored_revision = configuration_revision(load_config())
    if restored_revision != expected_revision:
        raise AtomicConfigurationRestoreError(
            "Rollback verification failed"
        )


def apply_configuration_restore(
    *,
    snapshot_path: Path,
    backup_output: Path,
    expected_current_revision: str,
    confirmation: str,
) -> dict[str, Any]:
    snapshot = load_snapshot_file(snapshot_path)
    candidate_config = validate_configuration_snapshot(snapshot)
    snapshot_revision = configuration_revision(candidate_config)
    backup_path = backup_output.expanduser().resolve()

    with configuration_write_lock():
        locked_current_revision = configuration_revision(load_config())
        if locked_current_revision != expected_current_revision:
            raise AtomicConfigurationRestoreError(
                "Current configuration revision changed before backup"
            )

        backup_result = create_verified_pre_restore_backup(
            snapshot_path=snapshot_path,
            backup_output=backup_output,
            expected_current_revision=expected_current_revision,
            confirmation=confirmation,
        )

        planned_snapshot_revision = backup_result.get(
            "snapshot_revision",
            snapshot_revision,
        )
        if planned_snapshot_revision != snapshot_revision:
            _remove_owned_backup(backup_path)
            raise AtomicConfigurationRestoreError(
                "Restore snapshot changed after initial validation"
            )

        if backup_result["backup_revision"] != locked_current_revision:
            _remove_owned_backup(backup_path)
            raise AtomicConfigurationRestoreError(
                "Verified backup revision does not match locked configuration"
            )

        immediate_current_revision = configuration_revision(load_config())
        if immediate_current_revision != expected_current_revision:
            _remove_owned_backup(backup_path)
            raise AtomicConfigurationRestoreError(
                "Current configuration revision changed immediately before write"
            )

        try:
            _save_config_unlocked(candidate_config)
        except Exception:
            # The atomic writer preserves the previous configuration when its
            # replacement fails. The verified backup remains available.
            raise

        try:
            written_revision = configuration_revision(load_config())
            if written_revision != snapshot_revision:
                raise AtomicConfigurationRestoreError(
                    "Restored configuration revision does not match snapshot"
                )
        except Exception as exc:
            _restore_verified_backup(
                backup_path,
                expected_current_revision,
            )
            raise AtomicConfigurationRestoreError(
                "Restore verification failed; original configuration restored"
            ) from exc

    return {
        "restore_applied": True,
        "previous_revision": expected_current_revision,
        "restored_revision": snapshot_revision,
        "backup_output": str(backup_path),
        "backup_revision": backup_result["backup_revision"],
        "configuration_write": "PERFORMED",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Apply a validated configuration snapshot under the shared write "
            "lock after creating a verified pre-restore backup."
        )
    )
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--backup-output", required=True, type=Path)
    parser.add_argument("--expected-current-revision", required=True)
    parser.add_argument("--confirm", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = apply_configuration_restore(
        snapshot_path=args.snapshot,
        backup_output=args.backup_output,
        expected_current_revision=args.expected_current_revision,
        confirmation=args.confirm,
    )

    print("configuration_restore: APPLIED")
    print(f"previous_revision: {result['previous_revision']}")
    print(f"restored_revision: {result['restored_revision']}")
    print(f"backup_output: {result['backup_output']}")
    print(f"backup_revision: {result['backup_revision']}")
    print("configuration_write: PERFORMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
