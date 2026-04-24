from __future__ import annotations

from urllib.parse import urlparse

from fastapi import HTTPException, Request, status

from app.core.config import settings


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_EXEMPT_PATHS = {
    f"{settings.api_prefix}/auth/login",
    f"{settings.api_prefix}/v1/auth/token",
    f"{settings.api_prefix}/v1/auth/refresh",
}


def should_validate_unsafe_api_request(request: Request) -> bool:
    if request.method.upper() in SAFE_METHODS:
        return False
    if not request.url.path.startswith(settings.api_prefix):
        return False
    if request.url.path in CSRF_EXEMPT_PATHS:
        return False
    authorization = request.headers.get("authorization", "").strip().lower()
    if authorization.startswith("bearer "):
        return False
    return True


def enforce_trusted_request_origin(request: Request) -> None:
    origin = _extract_request_origin(request)
    if not origin:
        if settings.allow_originless_unsafe_api_requests:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unsafe requests must include a trusted Origin or Referer header.",
        )

    if origin not in set(settings.csrf_trusted_origins):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request origin is not allowed.",
        )


def enforce_csrf_token(request: Request) -> None:
    if request.method.upper() in SAFE_METHODS:
        return
    if request.url.path in CSRF_EXEMPT_PATHS:
        return

    session_user_id = request.session.get("user_id")
    if session_user_id is None:
        return

    expected_token = str(request.session.get("csrf_token") or "")
    provided_token = request.headers.get("x-csrf-token", "").strip()
    if not expected_token or not provided_token or provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed.",
        )


def _extract_request_origin(request: Request) -> str | None:
    origin = request.headers.get("origin", "").strip()
    if origin:
        parsed = urlparse(origin)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".lower()

    referer = request.headers.get("referer", "").strip()
    if not referer:
        return None

    parsed_referer = urlparse(referer)
    if not parsed_referer.scheme or not parsed_referer.netloc:
        return None
    return f"{parsed_referer.scheme}://{parsed_referer.netloc}".lower()
