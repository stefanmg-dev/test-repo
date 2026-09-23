import logging
from dataclasses import dataclass
from pathlib import Path

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Engine, text


logger = logging.getLogger("document_processing.startup")
PROJECT_ROOT = Path(__file__).resolve().parent
ALEMBIC_CONFIG_PATH = PROJECT_ROOT / "alembic.ini"


class StartupValidationError(RuntimeError):
    pass


@dataclass(frozen=True)
class StartupValidationResult:
    database_connected: bool
    current_revisions: tuple[str, ...]
    expected_revisions: tuple[str, ...]


def get_expected_revisions(
    config_path: Path = ALEMBIC_CONFIG_PATH,
) -> tuple[str, ...]:
    config = Config(str(config_path))
    script_directory = ScriptDirectory.from_config(config)
    return tuple(sorted(script_directory.get_heads()))


def validate_database_startup(
    engine: Engine,
    *,
    config_path: Path = ALEMBIC_CONFIG_PATH,
) -> StartupValidationResult:
    try:
        expected_revisions = get_expected_revisions(
            config_path
        )
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            current_revisions = tuple(
                sorted(
                    MigrationContext.configure(
                        connection
                    ).get_current_heads()
                )
            )
    except Exception as exc:
        raise StartupValidationError(
            "Database startup validation failed"
        ) from exc

    if current_revisions != expected_revisions:
        raise StartupValidationError(
            "Database migration revision mismatch: "
            f"current={current_revisions or ('base',)}, "
            f"expected={expected_revisions}"
        )

    result = StartupValidationResult(
        database_connected=True,
        current_revisions=current_revisions,
        expected_revisions=expected_revisions,
    )
    logger.info(
        "Application startup validation completed",
        extra={
            "event": "application.startup_validated",
        },
    )
    return result
