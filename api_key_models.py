from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from security_scopes import (
    ADMIN,
    CONFIG_READ,
    CONFIG_WRITE,
    DOCUMENTS_EXTRACT,
    PROCESSING_RUNS_READ,
)


ALLOWED_API_KEY_SCOPES = {
    DOCUMENTS_EXTRACT,
    PROCESSING_RUNS_READ,
    CONFIG_READ,
    CONFIG_WRITE,
    ADMIN,
}


class ApiKeyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    scopes: set[str] = Field(min_length=1)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_scopes(self):
        unknown = self.scopes - ALLOWED_API_KEY_SCOPES
        if unknown:
            raise ValueError(f"Unknown API key scopes: {sorted(unknown)}")
        if self.expires_at is not None:
            from datetime import timezone
            current = datetime.now(timezone.utc)
            expires_at = self.expires_at
            if expires_at.tzinfo is None:
                raise ValueError("expires_at must include a timezone")
            if expires_at <= current:
                raise ValueError("expires_at must be in the future")
        return self


class ApiKeyRotateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expires_at: datetime | None = None


class ApiKeyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    name: str
    tenant_id: str
    secret_prefix: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None


class ApiKeyCreatedModel(ApiKeyModel):
    secret: str


class ApiKeyListResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ApiKeyModel]
