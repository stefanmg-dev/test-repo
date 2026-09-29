import json
import logging
from io import StringIO

from logging_config import JsonLogFormatter
from security_audit import audit_security_event
from security_principal import SecurityPrincipal


def test_security_audit_emits_safe_structured_context():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    logger = logging.getLogger("document_processing.security")
    previous_handlers = logger.handlers
    previous_propagate = logger.propagate
    previous_level = logger.level
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    principal = SecurityPrincipal(
        principal_type="service",
        subject="service-1",
        tenant_id="tenant-1",
        scopes=frozenset({"config:read"}),
    )
    try:
        audit_security_event(
            "security.authorization_denied",
            message="Authorization scope denied",
            result="denied",
            principal=principal,
            required_scope="config:write",
            api_key_id="key-1",
            authentication_method="api_key",
        )
    finally:
        logger.handlers = previous_handlers
        logger.propagate = previous_propagate
        logger.setLevel(previous_level)

    payload = json.loads(stream.getvalue())
    assert payload["event"] == "security.authorization_denied"
    assert payload["result"] == "denied"
    assert payload["principal_type"] == "service"
    assert payload["principal_subject"] == "service-1"
    assert payload["tenant_id"] == "tenant-1"
    assert payload["required_scope"] == "config:write"
    assert payload["api_key_id"] == "key-1"
    assert payload["authentication_method"] == "api_key"


def test_security_audit_never_accepts_secret_fields():
    record = logging.LogRecord(
        name="document_processing.security",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Authentication failed",
        args=(),
        exc_info=None,
    )
    record.api_key = "dpk_prefix_raw-secret"
    record.bearer_token = "sensitive-token"
    record.secret_hash = "sensitive-hash"
    record.event = "security.authentication_failed"

    serialized = JsonLogFormatter().format(record)
    assert "raw-secret" not in serialized
    assert "sensitive-token" not in serialized
    assert "sensitive-hash" not in serialized


def test_processing_review_audit_contains_no_document_values():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    logger = logging.getLogger("document_processing.security")
    previous_handlers = logger.handlers
    previous_propagate = logger.propagate
    previous_level = logger.level
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    principal = SecurityPrincipal(
        principal_type="user",
        subject="reviewer-1",
        tenant_id="tenant-1",
        scopes=frozenset({"processing-runs:review"}),
    )

    try:
        audit_security_event(
            "security.processing_review_corrected",
            message="Processing review decision recorded",
            result="success",
            principal=principal,
            processing_run_id="run-1",
            review_decision="corrected",
        )
    finally:
        logger.handlers = previous_handlers
        logger.propagate = previous_propagate
        logger.setLevel(previous_level)

    payload = json.loads(stream.getvalue())

    assert payload["event"] == (
        "security.processing_review_corrected"
    )
    assert payload["processing_run_id"] == "run-1"
    assert payload["review_decision"] == "corrected"
    assert payload["principal_subject"] == "reviewer-1"
    assert "final_values" not in payload
    assert "corrected_values" not in payload


def test_retention_audit_contains_only_operational_metadata():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    logger = logging.getLogger("document_processing.security")
    previous_handlers = logger.handlers
    previous_propagate = logger.propagate
    previous_level = logger.level
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    principal = SecurityPrincipal(
        principal_type="service",
        subject="retention-admin",
        tenant_id="tenant-1",
        scopes=frozenset({"admin"}),
    )
    try:
        audit_security_event(
            "security.processing_retention_executed",
            message="Processing run retention executed",
            result="success",
            principal=principal,
            retention_cutoff="2025-09-27T00:00:00+00:00",
            retention_limit=100,
            deleted_count=2,
        )
    finally:
        logger.handlers = previous_handlers
        logger.propagate = previous_propagate
        logger.setLevel(previous_level)

    payload = json.loads(stream.getvalue())
    assert payload["retention_limit"] == 100
    assert payload["deleted_count"] == 2
    assert payload["tenant_id"] == "tenant-1"
    assert "final_values" not in payload
    assert "corrected_values" not in payload


def test_feedback_export_audit_contains_only_operational_metadata():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    logger = logging.getLogger("document_processing.security")
    previous_handlers = logger.handlers
    previous_propagate = logger.propagate
    previous_level = logger.level
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    principal = SecurityPrincipal(
        principal_type="service",
        subject="feedback-reader",
        tenant_id="tenant-1",
        scopes=frozenset({"processing-runs:read"}),
    )
    try:
        audit_security_event(
            "security.processing_invoice_feedback_exported",
            message="Universal Invoice feedback exported",
            result="success",
            principal=principal,
            feedback_export_limit=100,
            cursor_supplied=True,
            exported_count=2,
            next_cursor_available=True,
        )
    finally:
        logger.handlers = previous_handlers
        logger.propagate = previous_propagate
        logger.setLevel(previous_level)

    payload = json.loads(stream.getvalue())
    assert payload["feedback_export_limit"] == 100
    assert payload["cursor_supplied"] is True
    assert payload["exported_count"] == 2
    assert payload["next_cursor_available"] is True
    assert payload["tenant_id"] == "tenant-1"
    forbidden = {
        "final_values",
        "corrected_values",
        "filename",
        "raw_text",
        "after_reviewed_at",
        "after_processing_run_id",
        "api_key",
    }
    assert forbidden.isdisjoint(payload)
    assert payload["processing_run_id"] is None
