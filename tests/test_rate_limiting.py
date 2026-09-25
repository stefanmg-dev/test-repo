from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app_settings import AppSettings
from rate_limit_middleware import create_rate_limit_middleware
from rate_limiting import ApplicationRateLimiter, safe_identity


def settings(**overrides):
    return AppSettings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
        **overrides,
    )


def test_disabled_rate_limiting_is_transparent():
    app = FastAPI()
    configured = settings(RATE_LIMIT_ENABLED=False)
    app.middleware("http")(
        create_rate_limit_middleware(
            configured,
            ApplicationRateLimiter("memory://"),
        )
    )

    @app.post("/extract-document")
    def extract():
        return {"ok": True}

    client = TestClient(app)
    assert all(
        client.post("/extract-document").status_code == 200
        for _ in range(3)
    )


def test_extract_limit_returns_429_and_retry_after():
    app = FastAPI()
    configured = settings(
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_EXTRACT_PER_MINUTE=1,
    )
    app.middleware("http")(
        create_rate_limit_middleware(
            configured,
            ApplicationRateLimiter("memory://"),
        )
    )

    @app.post("/extract-document")
    def extract():
        return {"ok": True}

    client = TestClient(app)
    assert client.post("/extract-document").status_code == 200
    response = client.post("/extract-document")
    assert response.status_code == 429
    assert response.json() == {"detail": "Rate limit exceeded"}
    assert int(response.headers["Retry-After"]) >= 1


def test_health_and_readiness_are_exempt():
    app = FastAPI()
    configured = settings(
        RATE_LIMIT_ENABLED=True,
        RATE_LIMIT_READ_PER_MINUTE=1,
    )
    app.middleware("http")(
        create_rate_limit_middleware(
            configured,
            ApplicationRateLimiter("memory://"),
        )
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    client = TestClient(app)
    assert all(client.get("/health").status_code == 200 for _ in range(3))


def test_production_rejects_memory_backend():
    with pytest.raises(ValidationError):
        settings(
            ENVIRONMENT="production",
            RATE_LIMIT_ENABLED=True,
            RATE_LIMIT_STORAGE_URI="memory://",
        )


def test_identity_is_stable_hash_not_raw_credential():
    raw = "dpk_prefix_secret"
    identity = safe_identity(raw)
    assert identity == safe_identity(raw)
    assert raw not in identity
    assert len(identity) == 64
