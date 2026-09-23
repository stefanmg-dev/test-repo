import logging
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import Request

from request_context import (
    reset_processing_run_id,
    reset_request_id,
    set_processing_run_id,
    set_request_id,
)


logger = logging.getLogger("document_processing.http")
REQUEST_ID_HEADER = "X-Request-ID"


def resolve_request_id(header_value: str | None) -> str:
    if header_value:
        try:
            return str(UUID(header_value))
        except ValueError:
            pass
    return str(uuid4())


async def request_logging_middleware(
    request: Request,
    call_next,
):
    request_id = resolve_request_id(
        request.headers.get(REQUEST_ID_HEADER)
    )
    request_token = set_request_id(request_id)
    processing_token = set_processing_run_id(None)
    request.state.request_id = request_id
    started_at = perf_counter()

    logger.info(
        "HTTP request started",
        extra={
            "event": "http.request_started",
            "http_method": request.method,
            "http_path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        duration_ms = max(
            0,
            round((perf_counter() - started_at) * 1000),
        )
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "HTTP request completed",
            extra={
                "event": "http.request_completed",
                "http_method": request.method,
                "http_path": request.url.path,
                "http_status": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
    except Exception as exc:
        logger.exception(
            "HTTP request failed",
            extra={
                "event": "http.request_failed",
                "http_method": request.method,
                "http_path": request.url.path,
                "duration_ms": max(
                    0,
                    round(
                        (perf_counter() - started_at) * 1000
                    ),
                ),
                "error_type": type(exc).__name__,
            },
        )
        raise
    finally:
        reset_processing_run_id(processing_token)
        reset_request_id(request_token)
