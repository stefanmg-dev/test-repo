from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from database_config import get_database_url


def create_database_engine(
    database_url: str | None = None,
) -> Engine:
    return create_engine(
        database_url or get_database_url(),
        pool_pre_ping=True,
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
