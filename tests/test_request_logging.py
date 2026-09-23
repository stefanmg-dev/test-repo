import json
import logging
from io import StringIO
from uuid import uuid4

from fastapi.testclient import TestClient

from api import app
from logging_config import JsonLogFormatter
from request_context import (
    reset_processing_run_id,
    reset_request_id,
    set_processing_run_id,
    set_request_id,
)


def test_request_id_is_generated_and_returned():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert str(
        uuid4().__class__(
            response.headers["X-Request-ID"]
        )
    ) == response.headers["X-Request-ID"]


def test_valid_request_id_is_preserved():
    request_id = str(uuid4())

    response = TestClient(app).get(
        "/health",
        headers={"X-Request-ID": request_id},
    )

    assert response.headers["X-Request-ID"] == request_id


def test_invalid_request_id_is_replaced():
    response = TestClient(app).get(
        "/health",
        headers={"X-Request-ID": "not-a-valid-uuid"},
    )

    assert response.headers["X-Request-ID"] != (
        "not-a-valid-uuid"
    )


def test_json_formatter_includes_correlation_context():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonLogFormatter())
    logger = logging.getLogger("test.structured")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    request_id = str(uuid4())
    processing_run_id = str(uuid4())
    request_token = set_request_id(request_id)
    processing_token = set_processing_run_id(
        processing_run_id
    )
    try:
        logger.info(
            "completed",
            extra={
                "event": "processing_run.completed",
                "duration_ms": 42,
            },
        )
    finally:
        reset_processing_run_id(processing_token)
        reset_request_id(request_token)

    payload = json.loads(stream.getvalue())

    assert payload["message"] == "completed"
    assert payload["request_id"] == request_id
    assert payload["processing_run_id"] == (
        processing_run_id
    )
    assert payload["event"] == (
        "processing_run.completed"
    )
    assert payload["duration_ms"] == 42


def test_json_formatter_excludes_unapproved_fields():
    record = logging.LogRecord(
        name="test.safe",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="safe",
        args=(),
        exc_info=None,
    )
    record.database_url = "postgres://user:secret@host/db"
    record.raw_text = "private document content"

    payload = json.loads(JsonLogFormatter().format(record))
    serialized = json.dumps(payload)

    assert "secret" not in serialized
    assert "private document content" not in serialized
    assert "database_url" not in payload
    assert "raw_text" not in payload
