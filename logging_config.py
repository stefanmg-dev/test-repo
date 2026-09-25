import json
import logging
from datetime import datetime, timezone
from typing import Any

from request_context import (
    get_processing_run_id,
    get_request_id,
)


STANDARD_LOG_RECORD_FIELDS = frozenset(
    logging.makeLogRecord({}).__dict__
)
SAFE_EXTRA_FIELDS = frozenset(
    {
        "api_key_id",
        "authentication_method",
        "duration_ms",
        "environment",
        "error_type",
        "event",
        "http_method",
        "http_path",
        "http_status",
        "input_format",
        "processing_status",
        "principal_subject",
        "principal_type",
        "profile",
        "required_scope",
        "result",
        "tenant_id",
    }
)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "processing_run_id": get_processing_run_id(),
        }

        for field in SAFE_EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        if record.exc_info:
            payload["exception_type"] = (
                record.exc_info[0].__name__
                if record.exc_info[0]
                else None
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(
    *,
    log_level: str,
    environment: str,
) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    logging.getLogger(__name__).info(
        "Application logging configured",
        extra={
            "event": "application.logging_configured",
            "environment": environment,
        },
    )
