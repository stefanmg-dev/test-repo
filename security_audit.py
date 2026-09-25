import logging
from typing import Any

from security_principal import SecurityPrincipal


logger = logging.getLogger("document_processing.security")


def audit_security_event(
    event: str,
    *,
    message: str,
    result: str,
    principal: SecurityPrincipal | None = None,
    required_scope: str | None = None,
    api_key_id: Any | None = None,
    authentication_method: str | None = None,
) -> None:
    extra = {
        "event": event,
        "result": result,
    }
    if principal is not None:
        extra.update(
            principal_type=principal.principal_type,
            principal_subject=principal.subject,
            tenant_id=principal.tenant_id,
        )
    if required_scope is not None:
        extra["required_scope"] = required_scope
    if api_key_id is not None:
        extra["api_key_id"] = str(api_key_id)
    if authentication_method is not None:
        extra["authentication_method"] = authentication_method

    logger.info(message, extra=extra)
