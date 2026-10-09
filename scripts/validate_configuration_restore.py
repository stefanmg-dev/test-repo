#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from typing import Any

from configuration_revision import configuration_revision
from configuration_snapshot import validate_configuration_snapshot
from config_store import load_config


def load_snapshot_file(snapshot_path: Path) -> dict[str, Any]:
    snapshot_path = snapshot_path.expanduser()

    try:
        content = snapshot_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Configuration snapshot was not found: {snapshot_path}"
        ) from exc

    try:
        snapshot = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in configuration snapshot: "
            f"line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(snapshot, dict):
        raise ValueError("Configuration snapshot root must be an object")

    return snapshot


def validate_restore_dry_run(snapshot_path: Path) -> dict[str, Any]:
    snapshot = load_snapshot_file(snapshot_path)
    candidate_config = validate_configuration_snapshot(snapshot)
    current_config = load_config()

    snapshot_revision = configuration_revision(candidate_config)
    current_revision = configuration_revision(current_config)

    return {
        "valid": True,
        "snapshot_revision": snapshot_revision,
        "current_revision": current_revision,
        "changes_detected": snapshot_revision != current_revision,
        "document_types": sorted(candidate_config),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a configuration snapshot as a restore candidate. "
            "This command is read-only and never modifies document_types.json."
        )
    )
    parser.add_argument(
        "snapshot",
        type=Path,
        help="Path to an exported .config-snapshot.json file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = validate_restore_dry_run(args.snapshot)

    print("restore_dry_run: VALID")
    print(f"snapshot_revision: {result['snapshot_revision']}")
    print(f"current_revision: {result['current_revision']}")
    print(f"changes_detected: {str(result['changes_detected']).lower()}")
    print(f"document_types: {','.join(result['document_types'])}")
    print("configuration_write: NOT_PERFORMED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
