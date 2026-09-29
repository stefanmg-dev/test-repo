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
    processing_run_id: Any | None = None,
    review_decision: str | None = None,
    retention_cutoff: Any | None = None,
    retention_limit: int | None = None,
    deleted_count: int | None = None,
    feedback_export_limit: int | None = None,
    cursor_supplied: bool | None = None,
    exported_count: int | None = None,
    next_cursor_available: bool | None = None,
    feedback_export_outcome: str | None = None,
    failure_reason: str | None = None,
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
    if processing_run_id is not None:
        extra["processing_run_id"] = str(processing_run_id)
    if review_decision is not None:
        extra["review_decision"] = review_decision
    if retention_cutoff is not None:
        extra["retention_cutoff"] = str(retention_cutoff)
    if retention_limit is not None:
        extra["retention_limit"] = retention_limit
    if deleted_count is not None:
        extra["deleted_count"] = deleted_count
    if feedback_export_limit is not None:
        extra["feedback_export_limit"] = feedback_export_limit
    if cursor_supplied is not None:
        extra["cursor_supplied"] = cursor_supplied
    if exported_count is not None:
        extra["exported_count"] = exported_count
    if next_cursor_available is not None:
        extra["next_cursor_available"] = next_cursor_available
    if feedback_export_outcome is not None:
        extra["feedback_export_outcome"] = feedback_export_outcome
    if failure_reason is not None:
        extra["failure_reason"] = failure_reason

    logger.info(message, extra=extra)
