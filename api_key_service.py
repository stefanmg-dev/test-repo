import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api_key_repository import ApiKeyRepository
from database_models import ApiKey
from security_principal import SecurityPrincipal


API_KEY_MARKER = "dpk"
API_KEY_PREFIX_BYTES = 8
API_KEY_SECRET_BYTES = 32


@dataclass(frozen=True)
class CreatedApiKey:
    api_key: ApiKey
    secret: str


class ApiKeyService:
    def __init__(self, session: Session):
        self._session = session
        self._repository = ApiKeyRepository(session)

    def create_key(
        self,
        *,
        name: str,
        tenant_id: str,
        scopes: set[str],
        expires_at: datetime | None = None,
    ) -> CreatedApiKey:
        prefix = secrets.token_hex(API_KEY_PREFIX_BYTES)
        secret_part = secrets.token_urlsafe(API_KEY_SECRET_BYTES)
        secret = f"{API_KEY_MARKER}_{prefix}_{secret_part}"
        api_key = ApiKey(
            name=name,
            tenant_id=tenant_id,
            secret_prefix=prefix,
            secret_hash=self.hash_secret(secret),
            scopes=sorted(scopes),
            expires_at=expires_at,
        )
        self._repository.add(api_key)
        self._session.commit()
        self._session.refresh(api_key)
        return CreatedApiKey(api_key=api_key, secret=secret)

    def authenticate(
        self,
        secret: str,
        *,
        now: datetime | None = None,
    ) -> SecurityPrincipal | None:
        prefix = self.extract_prefix(secret)
        if prefix is None:
            return None
        api_key = self._repository.get_by_prefix(prefix)
        if api_key is None:
            return None
        current_time = now or datetime.now(timezone.utc)
        if api_key.revoked_at is not None:
            return None
        if api_key.expires_at is not None and api_key.expires_at <= current_time:
            return None
        if not hmac.compare_digest(
            api_key.secret_hash,
            self.hash_secret(secret),
        ):
            return None
        api_key.last_used_at = current_time
        self._session.commit()
        return SecurityPrincipal(
            principal_type="service",
            subject=str(api_key.id),
            tenant_id=api_key.tenant_id,
            scopes=frozenset(api_key.scopes),
        )

    def revoke(
        self,
        api_key: ApiKey,
        *,
        revoked_at: datetime | None = None,
    ) -> ApiKey:
        api_key.revoked_at = revoked_at or datetime.now(timezone.utc)
        self._session.commit()
        self._session.refresh(api_key)
        return api_key

    @staticmethod
    def hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    @staticmethod
    def extract_prefix(secret: str) -> str | None:
        parts = secret.split("_", 2)
        if len(parts) != 3 or parts[0] != API_KEY_MARKER:
            return None
        return parts[1] or None
