import json
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

    temporary_path = CONFIG_PATH.with_suffix(".json.tmp")

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8"
        ) as config_file:
            json.dump(
                config,
                config_file,
                ensure_ascii=False,
                indent=2
            )

            config_file.write("\n")

        temporary_path.replace(CONFIG_PATH)

    finally:
        if temporary_path.exists():
            temporary_path.unlink()