from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, ConfigDict, Field
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



class HealthResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        description="Application liveness status.",
        examples=["ok"],
    )


class ReadinessResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        description="Application readiness status.",
        examples=["ready"],
    )
    database: str = Field(
        description="Database connectivity status.",
        examples=["connected"],
    )
    migrations: str = Field(
        description="Database migration status.",
        examples=["current"],
    )
    revision: str | list[str] = Field(
        description=(
            "Current database migration revision, or multiple revisions when "
            "the migration graph has more than one active head."
        ),
        examples=["a6c3d4e5f7b8"],
    )


class ReadinessErrorResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        description="Readiness failure status.",
        examples=["not_ready"],
    )

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


@app.get(
    "/health",
    response_model=HealthResponseModel,
    summary="Health check",
    description=(
        "Reports application-process liveness without checking external "
        "dependencies."
    ),
    response_description="Application process is running.",
)
def health_check():
    return {
        "status": "ok"
    }

@app.get(
    "/ready",
    response_model=ReadinessResponseModel,
    summary="Readiness check",
    description=(
        "Checks database connectivity and confirms that database migrations "
        "are current before reporting the application as ready."
    ),
    response_description="Application dependencies are ready.",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessErrorResponseModel,
            "description": "Application dependencies are not ready.",
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


def custom_openapi():
    if app.openapi_schema is not None:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    components = schema.get("components", {}).get("schemas", {})

    http_validation = components.get("HTTPValidationError", {})
    detail = http_validation.get("properties", {}).get("detail")
    if detail is not None:
        detail["description"] = (
            "List of request validation errors detected in path, query, "
            "header, cookie, or body input."
        )
        detail["examples"] = [[
            {
                "type": "string_too_short",
                "loc": ["body", "name"],
                "msg": "String should have at least 1 character",
                "input": "",
                "ctx": {"min_length": 1},
            }
        ]]

    validation_error = components.get("ValidationError", {})
    properties = validation_error.get("properties", {})
    documentation = {
        "loc": (
            "Location of the invalid value, beginning with its request "
            "source and followed by nested field names or indexes."
        ),
        "msg": "Human-readable explanation of the validation failure.",
        "type": (
            "Machine-readable validation error code suitable for programmatic "
            "handling."
        ),
        "input": "Input value that failed validation, when available.",
        "ctx": (
            "Optional structured values used to format or explain the "
            "validation error."
        ),
    }
    examples = {
        "loc": [["body", "name"]],
        "msg": ["String should have at least 1 character"],
        "type": ["string_too_short"],
        "input": [""],
        "ctx": [{"min_length": 1}],
    }
    for name, description in documentation.items():
        field = properties.get(name)
        if field is not None:
            field["description"] = description
            field["examples"] = examples[name]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
