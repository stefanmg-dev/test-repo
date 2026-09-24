from sqlalchemy import select
from sqlalchemy.orm import Session

from database_models import ApiKey


class ApiKeyRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, api_key: ApiKey) -> ApiKey:
        self._session.add(api_key)
        self._session.flush()
        return api_key

    def get_by_prefix(self, secret_prefix: str) -> ApiKey | None:
        statement = select(ApiKey).where(
            ApiKey.secret_prefix == secret_prefix
        )
        return self._session.scalar(statement)
