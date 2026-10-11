from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from security_scopes import (
    ADMIN,
    CONFIG_READ,
    CONFIG_WRITE,
    DOCUMENTS_EXTRACT,
    PROCESSING_RUNS_READ,
    PROCESSING_RUNS_REVIEW,
)


ALLOWED_API_KEY_SCOPES = {
    DOCUMENTS_EXTRACT,
    PROCESSING_RUNS_READ,
    PROCESSING_RUNS_REVIEW,
    CONFIG_READ,
    CONFIG_WRITE,
    ADMIN,
}


class ApiKeyCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Human-readable name used to identify the API key.",
        examples=["document-import-service"],
    )
    scopes: set[str] = Field(
        min_length=1,
        description="Permission scopes granted to the API key.",
        examples=[["documents:extract", "processing-runs:read"]],
    )
    expires_at: datetime | None = Field(
        default=None,
        description=(
            "Optional future expiration timestamp including a timezone. "
            "Omit it for a key without a configured expiration."
        ),
        examples=["2027-01-31T23:59:59Z"],
    )

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

    expires_at: datetime | None = Field(
        default=None,
        description=(
            "Optional replacement expiration timestamp including a timezone. "
            "Omit it to preserve a non-expiring replacement key."
        ),
        examples=["2027-01-31T23:59:59Z"],
    )


class ApiKeyModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID = Field(
        description="Stable identifier of the API-key record.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    name: str = Field(
        description="Human-readable API-key name.",
        examples=["document-import-service"],
    )
    tenant_id: str = Field(
        description="Tenant boundary to which the API key belongs.",
        examples=["default"],
    )
    secret_prefix: str = Field(
        description="Non-secret prefix used to recognize the API key.",
        examples=["dpk_3f92a1"],
    )
    scopes: list[str] = Field(
        description="Permission scopes granted to the API key.",
        examples=[["documents:extract", "processing-runs:read"]],
    )
    created_at: datetime = Field(
        description="Timestamp when the API key was created.",
        examples=["2026-10-11T12:00:00Z"],
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Configured expiration timestamp, or null when unset.",
        examples=["2027-01-31T23:59:59Z"],
    )
    last_used_at: datetime | None = Field(
        default=None,
        description="Most recent successful use timestamp, or null if unused.",
        examples=["2026-10-12T08:30:00Z"],
    )
    revoked_at: datetime | None = Field(
        default=None,
        description="Revocation timestamp, or null while the key is active.",
        examples=[None],
    )


class ApiKeyCreatedModel(ApiKeyModel):
    secret: str = Field(
        description=(
            "New plaintext secret returned only by the create or rotate "
            "operation. Store it securely because it cannot be retrieved later."
        ),
        examples=["dpk_example_secret_value"],
    )


class ApiKeyListResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ApiKeyModel] = Field(
        description="API keys belonging to the authenticated administrator's tenant.",
    )
