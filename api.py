from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app_settings import get_settings
from database import engine
from logging_config import configure_logging
from rate_limit_middleware import create_rate_limit_middleware
from rate_limiting import ApplicationRateLimiter
from request_logging import request_logging_middleware
from startup_validation import validate_database_startup
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from routes_api_keys import router as api_keys_router
from routes_auth import router as auth_router
from routes_config_collections_v1 import (
    router as config_collections_v1_router,
)
from routes_config_v1 import router as config_v1_router
from routes_extract import router as extract_router
from routes_processing_runs import (
    router as processing_runs_router,
)


BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "ui"
SETTINGS = get_settings()

configure_logging(
    log_level=SETTINGS.log_level,
    environment=SETTINGS.environment,
)


@asynccontextmanager
async def application_lifespan(app: FastAPI):
    validate_database_startup(engine)
    yield
    engine.dispose()


docs_enabled = SETTINGS.api_docs_enabled()

app = FastAPI(
    title="Document Extraction API",
    version="1.0.0",
    lifespan=application_lifespan,
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=SETTINGS.allowed_hosts_list(),
)

cors_origins = SETTINGS.cors_allowed_origins_list()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Accept", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

rate_limiter = ApplicationRateLimiter(
    SETTINGS.rate_limit_storage_uri_value()
)
app.middleware("http")(
    create_rate_limit_middleware(SETTINGS, rate_limiter)
)
app.middleware("http")(request_logging_middleware)


app.include_router(extract_router)
app.include_router(api_keys_router)
app.include_router(auth_router)
app.include_router(processing_runs_router)
app.include_router(config_v1_router)
app.include_router(config_collections_v1_router)


app.mount(
    "/ui",
    StaticFiles(
        directory=UI_DIR,
        html=True,
    ),
    name="ui",
)


@app.get(
    "/",
    include_in_schema=False,
)
def open_ui():
    return RedirectResponse(
        url="/ui/index.html"
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }

@app.get(
    "/ready",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Application dependencies are not ready",
        },
    },
)
def readiness_check():
    try:
        result = validate_database_startup(engine)
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
            },
        )

    return {
        "status": "ready",
        "database": "connected",
        "migrations": "current",
        "revision": (
            result.current_revisions[0]
            if len(result.current_revisions) == 1
            else list(result.current_revisions)
        ),
    }
