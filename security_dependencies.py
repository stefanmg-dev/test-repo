from typing import Annotated, Callable

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from api_key_service import ApiKeyService
from database import get_database_session
from security_principal import SecurityPrincipal


api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Service API key",
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


async def get_optional_api_key_principal(
    api_key_service: ApiKeyServiceDependency,
    api_key: Annotated[
        str | None,
        Security(api_key_header),
    ] = None,
) -> SecurityPrincipal | None:
    if api_key is None:
        return None

    principal = api_key_service.authenticate(api_key)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "APIKey"},
        )
    return principal


OptionalApiKeyPrincipal = Annotated[
    SecurityPrincipal | None,
    Depends(get_optional_api_key_principal),
]


def require_scope(
    scope: str,
) -> Callable[[SecurityPrincipal], SecurityPrincipal]:
    async def dependency(
        principal: Annotated[
            SecurityPrincipal | None,
            Depends(get_optional_api_key_principal),
        ],
    ) -> SecurityPrincipal:
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "APIKey"},
            )
        if not principal.has_scope(scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )
        return principal

    return dependency
