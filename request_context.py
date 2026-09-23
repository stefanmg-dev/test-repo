from contextvars import ContextVar, Token


_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)
_processing_run_id: ContextVar[str | None] = ContextVar(
    "processing_run_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


def get_processing_run_id() -> str | None:
    return _processing_run_id.get()


def set_request_id(value: str | None) -> Token:
    return _request_id.set(value)


def set_processing_run_id(value: str | None) -> Token:
    return _processing_run_id.set(value)


def reset_request_id(token: Token) -> None:
    _request_id.reset(token)


def reset_processing_run_id(token: Token) -> None:
    _processing_run_id.reset(token)
