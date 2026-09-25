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
