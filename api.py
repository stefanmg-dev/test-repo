from fastapi import FastAPI

from routes_config import router as config_router
from routes_config_v1 import router as config_v1_router
from routes_extract import router as extract_router


app = FastAPI(
    title="Document Extraction API",
    version="1.0.0",
)


app.include_router(extract_router)
app.include_router(config_router)
app.include_router(config_v1_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }