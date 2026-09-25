from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app_settings import get_settings

from security_audit import audit_security_event
from security_dependencies import get_optional_principal
from security_principal import SecurityPrincipal


DOCUMENTS_EXTRACT = "documents:extract"
PROCESSING_RUNS_READ = "processing-runs:read"
CONFIG_READ = "config:read"
CONFIG_WRITE = "config:write"
ADMIN = "admin"


def enforce_scope_if_authenticated(
    principal: SecurityPrincipal | None,
    required_scope: str,
    *,
    legacy_anonymous_access_enabled: bool | None = None,
) -> None:
    """Enforce scope and optionally preserve transitional anonymous access."""
    if legacy_anonymous_access_enabled is None:
        legacy_anonymous_access_enabled = (
            get_settings().legacy_anonymous_access_enabled
        )
    if principal is None:
        if legacy_anonymous_access_enabled:
            return
        audit_security_event(
            "security.authentication_required",
            message="Authentication required",
            result="denied",
            required_scope=required_scope,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={
                "WWW-Authenticate": "APIKey, Bearer",
            },
        )
    if not principal.has_scope(required_scope):
        audit_security_event(
            "security.authorization_denied",
            message="Authorization scope denied",
            result="denied",
            principal=principal,
            required_scope=required_scope,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required scope: {required_scope}",
        )


async def enforce_config_scope(
    request: Request,
    principal: Annotated[
        SecurityPrincipal | None,
        Depends(get_optional_principal),
    ],
) -> None:
    required_scope = (
        CONFIG_READ
        if request.method == "GET"
        else CONFIG_WRITE
    )
    enforce_scope_if_authenticated(
        principal,
        required_scope,
    )
