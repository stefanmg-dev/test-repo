from pydantic import ValidationError

from app_settings import AppSettings, get_settings


def get_database_url() -> str:
    try:
        return get_settings().database_url_value()
    except ValidationError as exc:
        raise RuntimeError(
            "DATABASE_URL environment variable is required"
        ) from exc
