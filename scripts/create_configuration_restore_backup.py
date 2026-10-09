#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_configuration_snapshot import (
    export_configuration_snapshot,
)
from scripts.plan_configuration_restore import (
    build_restore_apply_plan,
)


def create_verified_pre_restore_backup(
    *,
    snapshot_path: Path,
    backup_output: Path,
    expected_current_revision: str,
    confirmation: str,
) -> dict[str, Any]:
    plan = build_restore_apply_plan(
        snapshot_path=snapshot_path,
        backup_output=backup_output,
        expected_current_revision=expected_current_revision,
        confirmation=confirmation,
    )

    backup_snapshot = export_configuration_snapshot(
        Path(plan["backup_output"])
    )

    if backup_snapshot["revision"] != plan["current_revision"]:
        backup_path = Path(plan["backup_output"])
        if backup_path.exists():
            backup_path.unlink()
        raise RuntimeError(
            "Pre-restore backup revision does not match current configuration"
        )

    return {
        **plan,
        "backup_created": True,
        "backup_revision": backup_snapshot["revision"],
        "configuration_write": "NOT_PERFORMED",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate restore preconditions and create a verified backup "
            "of the current configuration. The restore is not applied."
        )
    )
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--backup-output", required=True, type=Path)
    parser.add_argument("--expected-current-revision", required=True)
    parser.add_argument("--confirm", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = create_verified_pre_restore_backup(
        snapshot_path=args.snapshot,
        backup_output=args.backup_output,
        expected_current_revision=args.expected_current_revision,
        confirmation=args.confirm,
    )

    print("pre_restore_backup: VERIFIED")
    print(f"backup_output: {result['backup_output']}")
    print(f"backup_revision: {result['backup_revision']}")
    print("backup_created: true")
    print("configuration_write: NOT_PERFORMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
