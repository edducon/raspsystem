import warnings

from fastapi import HTTPException
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic.warnings import UnsupportedFieldAttributeWarning
from starlette.middleware.sessions import SessionMiddleware

import app.models  # noqa: F401
from app.api.router import api_router
from app.core.config import settings
from app.core.request_security import (
    enforce_csrf_token,
    enforce_trusted_request_origin,
    should_validate_unsafe_api_request,
)
from app.core.validation_errors import format_request_validation_error

# FastAPI + Pydantic on Python 3.14 emits this warning while composing request/response models,
# even though the generated OpenAPI/body schemas work correctly with our camelCase contract.
warnings.filterwarnings("ignore", category=UnsupportedFieldAttributeWarning)

settings.validate_runtime_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.are_api_docs_enabled else None,
    redoc_url="/redoc" if settings.are_api_docs_enabled else None,
    openapi_url="/openapi.json" if settings.are_api_docs_enabled else None,
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie=settings.session_cookie_name,
    max_age=settings.session_max_age,
    same_site=settings.session_same_site,
    https_only=settings.session_https_only,
    domain=settings.session_cookie_domain,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Content-Type", "X-CSRF-Token"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.middleware("http")
async def harden_requests(request: Request, call_next):
    try:
        if should_validate_unsafe_api_request(request):
            enforce_trusted_request_origin(request)
            enforce_csrf_token(request)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)

    response = await call_next(request)
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": format_request_validation_error(exc)},
    )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "RaspSystem backend is running",
        "docs": "/docs" if settings.are_api_docs_enabled else "disabled",
    }
