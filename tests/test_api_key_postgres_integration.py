import os
from datetime import datetime, timedelta, timezone

import pytest


if not os.getenv("DATABASE_URL"):
    pytest.skip(
        "DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

from api_key_service import ApiKeyService
from database import SessionLocal
from database_models import ApiKey


def test_api_key_lifecycle_in_postgresql():
    session = SessionLocal()
    api_key_id = None
    try:
        service = ApiKeyService(session)
        created = service.create_key(
            name="postgres integration",
            tenant_id="tenant-integration",
            scopes={"documents:extract", "processing-runs:read"},
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        api_key_id = created.api_key.id

        assert created.secret.startswith("dpk_")
        assert created.secret not in created.api_key.secret_hash
        assert len(created.api_key.secret_hash) == 64

        principal = service.authenticate(created.secret)
        assert principal is not None
        assert principal.tenant_id == "tenant-integration"
        assert principal.scopes == frozenset(
            {"documents:extract", "processing-runs:read"}
        )

        service.revoke(created.api_key)
        assert service.authenticate(created.secret) is None
    finally:
        session.rollback()
        if api_key_id is not None:
            persisted = session.get(ApiKey, api_key_id)
            if persisted is not None:
                session.delete(persisted)
                session.commit()
        session.close()
