#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configuration_snapshot import (
    build_configuration_snapshot,
    validate_configuration_snapshot,
)
from config_store import load_config


def export_configuration_snapshot(output_path: Path) -> dict:
    output_path = output_path.expanduser()
    if output_path.exists():
        raise FileExistsError(
            f"Snapshot destination already exists: {output_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot = build_configuration_snapshot(load_config())

    created_output = False

    try:
        with output_path.open(
            "x",
            encoding="utf-8",
        ) as output_file:
            created_output = True
            json.dump(
                snapshot,
                output_file,
                ensure_ascii=False,
                indent=2,
            )
            output_file.write("\n")

        written_snapshot = json.loads(
            output_path.read_text(encoding="utf-8")
        )
        validate_configuration_snapshot(written_snapshot)
    except Exception:
        if created_output and output_path.exists():
            output_path.unlink()
        raise

    return snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export the current validated document configuration "
            "as a versioned local snapshot."
        )
    )
    parser.add_argument(
        "output",
        type=Path,
        help=(
            "New output path. Existing files are never overwritten. "
            "Use configuration_snapshots/*.config-snapshot.json "
            "for ignored local artifacts."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot = export_configuration_snapshot(args.output)
    print(f"snapshot_path: {args.output.expanduser()}")
    print(f"snapshot_revision: {snapshot['revision']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
