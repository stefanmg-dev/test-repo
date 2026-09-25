from fastapi import Request
from fastapi.responses import JSONResponse

from app_settings import AppSettings
from rate_limiting import ApplicationRateLimiter, safe_identity
from security_audit import audit_security_event


EXEMPT_PATHS = {"/health", "/ready"}


def route_policy(request: Request, settings: AppSettings):
    path = request.url.path
    if path in EXEMPT_PATHS or path.startswith("/ui/"):
        return None
    if path == "/extract-document" and request.method == "POST":
        return "extract", settings.rate_limit_extract_per_minute
    if path.startswith("/api/v1/api-keys"):
        return "api_keys", settings.rate_limit_api_keys_per_minute
    if request.method == "GET" and (
        path.startswith("/api/v1/processing-runs")
        or path.startswith("/api/v1/config")
    ):
        return "read", settings.rate_limit_read_per_minute
    return None


def request_identity(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    authorization = request.headers.get("Authorization")
    if api_key:
        return "api-key:" + safe_identity(api_key)
    if authorization:
        return "authorization:" + safe_identity(authorization)
    peer = request.client.host if request.client else "unknown"
    return "peer:" + safe_identity(peer)


def create_rate_limit_middleware(
    settings: AppSettings,
    limiter: ApplicationRateLimiter,
):
    async def middleware(request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)
        policy = route_policy(request, settings)
        if policy is None:
            return await call_next(request)
        bucket, amount = policy
        decision = limiter.check(
            bucket=bucket,
            identity=request_identity(request),
            amount_per_minute=amount,
        )
        if decision.allowed:
            return await call_next(request)
        audit_security_event(
            "security.rate_limit_exceeded",
            message="Rate limit exceeded",
            result="denied",
            authentication_method="request_identity",
        )
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": str(decision.retry_after)},
        )

    return middleware
