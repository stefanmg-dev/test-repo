from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from database_config import get_database_url


def create_database_engine(
    database_url: str | None = None,
) -> Engine:
    settings = None
    if database_url is None:
        from app_settings import get_settings

        settings = get_settings()

    engine_options = {
        "pool_pre_ping": True,
    }
    if settings is not None:
        engine_options.update(
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=(
                settings.database_pool_timeout_seconds
            ),
        )

    return create_engine(
        database_url or settings.database_url_value(),
        **engine_options,
    )


engine = create_database_engine()
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_database_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
