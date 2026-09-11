from fastapi import FastAPI

from routes_extract import router as extract_router
from routes_config import router as config_router

app = FastAPI(
    title="Document Extraction API"
)

app.include_router(extract_router)
app.include_router(config_router)