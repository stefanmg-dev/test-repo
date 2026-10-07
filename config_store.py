import json
import os
import tempfile
from pathlib import Path

from config_validator import validate_config


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "document_types.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {CONFIG_PATH}"
        )

    try:
        with CONFIG_PATH.open(
            "r",
            encoding="utf-8"
        ) as config_file:
            config = json.load(config_file)

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {CONFIG_PATH.name}: "
            f"line {exc.lineno}, column {exc.colno}: "
            f"{exc.msg}"
        ) from exc

    validate_config(config)

    return config


def save_config(config: dict) -> None:
    validate_config(config)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{CONFIG_PATH.name}.",
        suffix=".tmp",
        dir=CONFIG_PATH.parent,
        text=True,
    )
    temporary_path = Path(temporary_name)

    try:
        config_file = os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
        )
        descriptor = None

        with config_file:
            json.dump(
                config,
                config_file,
                ensure_ascii=False,
                indent=2,
            )
            config_file.write("\n")
            config_file.flush()
            os.fsync(config_file.fileno())

        os.replace(temporary_path, CONFIG_PATH)

    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_path.exists():
            temporary_path.unlink()
