from functools import lru_cache
from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import (
    APIKeyHeader,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from api_key_service import ApiKeyService
from app_settings import get_settings
from database import get_database_session
from oidc_token_validator import (
    OidcTokenValidationError,
    OidcTokenValidator,
)
from security_audit import audit_security_event
from security_principal import SecurityPrincipal


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Service API key",
    auto_error=False,
)


bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="OIDC access token",
    auto_error=False,
)

DatabaseSession = Annotated[
    Session,
    Depends(get_database_session),
]


def get_api_key_service(
    session: DatabaseSession,
) -> ApiKeyService:
    return ApiKeyService(session)


ApiKeyServiceDependency = Annotated[
    ApiKeyService,
    Depends(get_api_key_service),
]


@lru_cache(maxsize=1)
def get_oidc_token_validator() -> OidcTokenValidator | None:
    settings = get_settings()
    if not settings.oidc_enabled:
        return None
    return OidcTokenValidator(settings)


OidcTokenValidatorDependency = Annotated[
    OidcTokenValidator | None,
    Depends(get_oidc_token_validator),
]


async def get_optional_principal(
    api_key_service: ApiKeyServiceDependency,
    oidc_validator: OidcTokenValidatorDependency = None,
    api_key: Annotated[
        str | None,
        Security(api_key_header),
    ] = None,
    bearer: Annotated[
        HTTPAuthorizationCredentials | None,
        Security(bearer_scheme),
    ] = None,
) -> SecurityPrincipal | None:
    if api_key is not None and bearer is not None:
        audit_security_event(
            "security.authentication_rejected",
            message="Multiple authentication mechanisms rejected",
            result="denied",
            authentication_method="multiple",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either X-API-Key or Bearer token, not both",
        )

    if api_key is not None:
        principal = api_key_service.authenticate(api_key)
        if principal is None:
            audit_security_event(
                "security.authentication_failed",
                message="API key authentication failed",
                result="denied",
                authentication_method="api_key",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "APIKey"},
            )
        return principal

    if bearer is not None:
        if oidc_validator is None:
            audit_security_event(
                "security.authentication_failed",
                message="Bearer authentication is disabled",
                result="denied",
                authentication_method="bearer",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer authentication is not enabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            return oidc_validator.validate(bearer.credentials)
        except OidcTokenValidationError as exc:
            audit_security_event(
                "security.authentication_failed",
                message="Bearer authentication failed",
                result="denied",
                authentication_method="bearer",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

    return None


# Backward-compatible symbol for existing overrides and imports.
get_optional_api_key_principal = get_optional_principal


OptionalPrincipal = Annotated[
    SecurityPrincipal | None,
    Depends(get_optional_principal),
]
OptionalApiKeyPrincipal = OptionalPrincipal


def require_scope(
    scope: str,
) -> Callable[[SecurityPrincipal], SecurityPrincipal]:
    async def dependency(
        principal: Annotated[
            SecurityPrincipal | None,
            Depends(get_optional_principal),
        ],
    ) -> SecurityPrincipal:
        if principal is None:
            audit_security_event(
                "security.authentication_required",
                message="Authentication required",
                result="denied",
                required_scope=scope,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "APIKey"},
            )
        if not principal.has_scope(scope):
            audit_security_event(
                "security.authorization_denied",
                message="Authorization scope denied",
                result="denied",
                principal=principal,
                required_scope=scope,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )
        return principal

    return dependency


AdminPrincipal = Annotated[
    SecurityPrincipal,
    Depends(require_scope("admin")),
]
