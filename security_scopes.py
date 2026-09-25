from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

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
) -> None:
    """Enforce least privilege while legacy anonymous access remains enabled."""
    if principal is None:
        return
    if not principal.has_scope(required_scope):
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
