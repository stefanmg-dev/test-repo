import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"


def load_environment() -> None:
    if ENV_FILE.is_file():
        load_dotenv(
            dotenv_path=ENV_FILE,
            override=False,
        )


def get_database_url() -> str:
    load_environment()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is required"
        )
    return database_url
