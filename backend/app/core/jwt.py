from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings


def create_access_token(
    user_id: int,
    role: str,
    flags: dict[str, bool],
    expires_delta: timedelta | None = None,
) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "role": role,
        "flags": flags,
    }
    return _encode_token(payload, expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))


def create_refresh_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    payload = {
        "sub": str(user_id),
        "type": "refresh",
    }
    return _encode_token(payload, expires_delta or timedelta(days=settings.jwt_refresh_token_expire_days))


def create_service_token(
    user_id: int,
    role: str,
    flags: dict[str, bool],
    expires_delta: timedelta | None = None,
) -> str:
    payload = {
        "sub": str(user_id),
        "type": "service",
        "role": role,
        "flags": flags,
    }
    return _encode_token(payload, expires_delta or timedelta(days=365))


def verify_token(token: str) -> dict[str, Any]:
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
    except ValueError as exc:
        raise _unauthorized("Invalid token format.") from exc

    header = _decode_segment(header_segment)
    if header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise _unauthorized("Invalid token header.")

    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    expected_signature = _b64url_encode(_sign(signing_input))
    if not hmac.compare_digest(signature_segment, expected_signature):
        raise _unauthorized("Invalid token signature.")

    payload = _decode_segment(payload_segment)
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise _unauthorized("Token expiration is missing.")
    if datetime.now(UTC).timestamp() >= exp:
        raise _unauthorized("Token has expired.")

    return payload


def _encode_token(payload: dict[str, Any], expires_delta: timedelta) -> str:
    issued_at = datetime.now(UTC)
    token_payload = {
        **payload,
        "iat": int(issued_at.timestamp()),
        "exp": int((issued_at + expires_delta).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}

    header_segment = _b64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    payload_segment = _b64url_encode(json.dumps(token_payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    signing_input = f"{header_segment}.{payload_segment}".encode("ascii")
    signature_segment = _b64url_encode(_sign(signing_input))
    return f"{header_segment}.{payload_segment}.{signature_segment}"


def _decode_segment(segment: str) -> dict[str, Any]:
    try:
        decoded = base64.urlsafe_b64decode(_pad_b64(segment))
        value = json.loads(decoded)
    except (ValueError, json.JSONDecodeError) as exc:
        raise _unauthorized("Invalid token payload.") from exc

    if not isinstance(value, dict):
        raise _unauthorized("Invalid token payload.")
    return value


def _sign(value: bytes) -> bytes:
    return hmac.new(settings.jwt_secret_key.encode("utf-8"), value, hashlib.sha256).digest()


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _pad_b64(value: str) -> bytes:
    return f"{value}{'=' * (-len(value) % 4)}".encode("ascii")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
