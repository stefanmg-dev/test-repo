#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_configuration_restore import (
    validate_restore_dry_run,
)


RESTORE_CONFIRMATION = "RESTORE"


class RestoreApplyPlanError(ValueError):
    pass


def build_restore_apply_plan(
    *,
    snapshot_path: Path,
    backup_output: Path,
    expected_current_revision: str,
    confirmation: str,
) -> dict[str, Any]:
    if confirmation != RESTORE_CONFIRMATION:
        raise RestoreApplyPlanError(
            "Restore confirmation must be exactly RESTORE"
        )

    result = validate_restore_dry_run(snapshot_path)
    current_revision = result["current_revision"]

    if expected_current_revision != current_revision:
        raise RestoreApplyPlanError(
            "Current configuration revision changed; rerun the dry-run"
        )

    snapshot_path = snapshot_path.expanduser().resolve()
    backup_output = backup_output.expanduser().resolve()

    if backup_output == snapshot_path:
        raise RestoreApplyPlanError(
            "Backup output must differ from the restore snapshot"
        )

    if backup_output.exists():
        raise FileExistsError(
            f"Backup destination already exists: {backup_output}"
        )

    return {
        "plan_valid": True,
        "snapshot_path": str(snapshot_path),
        "snapshot_revision": result["snapshot_revision"],
        "current_revision": current_revision,
        "changes_detected": result["changes_detected"],
        "backup_output": str(backup_output),
        "backup_required": True,
        "configuration_write": "NOT_PERFORMED",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate configuration restore apply preconditions. "
            "This command creates only a plan and performs no writes."
        )
    )
    parser.add_argument(
        "snapshot",
        type=Path,
        help="Validated restore candidate snapshot.",
    )
    parser.add_argument(
        "--backup-output",
        required=True,
        type=Path,
        help="Required new path for the pre-restore backup.",
    )
    parser.add_argument(
        "--expected-current-revision",
        required=True,
        help="Current revision observed during the preceding dry-run.",
    )
    parser.add_argument(
        "--confirm",
        required=True,
        help="Must be exactly RESTORE.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_restore_apply_plan(
        snapshot_path=args.snapshot,
        backup_output=args.backup_output,
        expected_current_revision=args.expected_current_revision,
        confirmation=args.confirm,
    )

    print("restore_apply_plan: VALID")
    print(f"snapshot_revision: {plan['snapshot_revision']}")
    print(f"current_revision: {plan['current_revision']}")
    print(f"changes_detected: {str(plan['changes_detected']).lower()}")
    print(f"backup_output: {plan['backup_output']}")
    print("backup_required: true")
    print("configuration_write: NOT_PERFORMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
