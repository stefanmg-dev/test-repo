from fastapi import HTTPException, status

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
