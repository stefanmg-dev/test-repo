from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, status

from app_settings import get_settings
from database import engine
from logging_config import configure_logging
from request_logging import request_logging_middleware
from startup_validation import validate_database_startup
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

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


app = FastAPI(
    title="Document Extraction API",
    version="1.0.0",
    lifespan=application_lifespan,
)


app.middleware("http")(request_logging_middleware)


app.include_router(extract_router)
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
