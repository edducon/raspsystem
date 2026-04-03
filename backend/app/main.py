from fastapi import FastAPI

import app.models  # noqa: F401
from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "RaspSystem backend is running",
        "docs": "/docs",
    }
