from uuid import UUID

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


    def get(
        self,
        api_key_id: UUID,
        *,
        tenant_id: str,
    ) -> ApiKey | None:
        statement = select(ApiKey).where(
            ApiKey.id == api_key_id,
            ApiKey.tenant_id == tenant_id,
        )
        return self._session.scalar(statement)

    def list_for_tenant(self, tenant_id: str) -> list[ApiKey]:
        statement = (
            select(ApiKey)
            .where(ApiKey.tenant_id == tenant_id)
            .order_by(ApiKey.created_at.desc(), ApiKey.id.desc())
        )
        return list(self._session.scalars(statement).all())
