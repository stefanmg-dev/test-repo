from datetime import datetime, timedelta, timezone
from unittest.mock import Mock
from uuid import uuid4

from api_key_service import ApiKeyService
from database_models import ApiKey


def test_extracts_only_canonical_api_key_prefix():
    assert ApiKeyService.extract_prefix("dpk_prefix_secret") == "prefix"
    assert ApiKeyService.extract_prefix("wrong_prefix_secret") is None
    assert ApiKeyService.extract_prefix("invalid") is None


def test_authenticates_active_key_as_service_principal():
    session = Mock()
    service = ApiKeyService(session)
    secret = "dpk_prefix_secret"
    api_key = ApiKey(
        id=uuid4(),
        name="integration",
        tenant_id="tenant-1",
        secret_prefix="prefix",
        secret_hash=service.hash_secret(secret),
        scopes=["documents:extract"],
        created_at=datetime.now(timezone.utc),
    )
    session.scalar.return_value = api_key

    principal = service.authenticate(secret)

    assert principal is not None
    assert principal.principal_type == "service"
    assert principal.subject == str(api_key.id)
    assert principal.tenant_id == "tenant-1"
    assert principal.scopes == frozenset({"documents:extract"})
    assert api_key.last_used_at is not None
    session.commit.assert_called_once_with()


def test_rejects_expired_revoked_and_wrong_secrets():
    now = datetime.now(timezone.utc)
    for api_key, secret in [
        (
            ApiKey(
                id=uuid4(), name="expired", tenant_id="t",
                secret_prefix="p", secret_hash=ApiKeyService.hash_secret("dpk_p_s"),
                scopes=[], created_at=now - timedelta(days=2),
                expires_at=now - timedelta(days=1),
            ),
            "dpk_p_s",
        ),
        (
            ApiKey(
                id=uuid4(), name="revoked", tenant_id="t",
                secret_prefix="p", secret_hash=ApiKeyService.hash_secret("dpk_p_s"),
                scopes=[], created_at=now, revoked_at=now,
            ),
            "dpk_p_s",
        ),
        (
            ApiKey(
                id=uuid4(), name="wrong", tenant_id="t",
                secret_prefix="p", secret_hash=ApiKeyService.hash_secret("dpk_p_correct"),
                scopes=[], created_at=now,
            ),
            "dpk_p_wrong",
        ),
    ]:
        session = Mock()
        session.scalar.return_value = api_key
        assert ApiKeyService(session).authenticate(secret, now=now) is None
        session.commit.assert_not_called()
