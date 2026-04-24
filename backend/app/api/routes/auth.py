from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limiter import get_rate_limiter
from app.db.session import get_db
from app.schemas.auth import (
    AuthChangePasswordRequest,
    AuthLoginRequest,
    AuthResponse,
    AuthUserRead,
    MessageResponse,
)
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _serialize_user(user) -> AuthUserRead:
    return AuthUserRead.model_validate(
        {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "can_schedule_semester": user.can_schedule_semester,
            "can_schedule_session": user.can_schedule_session,
            "can_schedule_retakes": user.can_schedule_retakes,
            "department_id": user.department_id,
            "department_ids": list(user.department_ids or []),
            "teacher_uuid": user.teacher_uuid,
            "must_change_password": user.must_change_password,
        }
    )


def _client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def _login_limit_keys(request: Request, username: str) -> list[str]:
    normalized_username = username.strip().lower()
    return [
        f"auth:login:ip:{_client_ip(request)}",
        f"auth:login:user:{normalized_username}",
    ]


def _password_change_limit_keys(request: Request, user_id: int) -> list[str]:
    return [
        f"auth:password-change:ip:{_client_ip(request)}",
        f"auth:password-change:user:{user_id}",
    ]


@router.post("/login", response_model=AuthResponse)
def login(
    payload: AuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    limiter = get_rate_limiter()
    audit = AuditService(db)
    limit_keys = _login_limit_keys(request, payload.username)
    limiter.ensure_within_limit(
        limit_keys,
        settings.login_rate_limit_attempts,
        settings.login_rate_limit_window_seconds,
        "Слишком много попыток входа. Повторите позже.",
    )

    service = AuthService(db)
    try:
        user = service.login(request=request, username=payload.username, password=payload.password)
    except HTTPException as exc:
        limiter.record_failure(limit_keys, settings.login_rate_limit_window_seconds)
        audit.record(
            action="auth.login",
            request=request,
            status="FAILURE",
            details={"username": payload.username, "status_code": exc.status_code},
        )
        raise

    limiter.reset(limit_keys)
    audit.record(
        action="auth.login",
        actor=user,
        request=request,
        status="SUCCESS",
        details={"username": user.username},
    )
    return AuthResponse(
        user=_serialize_user(user),
        csrf_token=service.get_csrf_token(request),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)) -> Response:
    service = AuthService(db)
    user = service.get_current_user(request)
    AuditService(db).record(
        action="auth.logout",
        actor=user,
        request=request,
        status="SUCCESS",
        details={"username": user.username},
    )
    service.logout(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AuthResponse)
def me(request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    service = AuthService(db)
    user = service.get_current_user(request)
    return AuthResponse(
        user=_serialize_user(user),
        csrf_token=service.get_csrf_token(request),
    )


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: AuthChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    audit = AuditService(db)
    user = service.get_current_user(request)
    limit_keys = _password_change_limit_keys(request, user.id)
    limiter = get_rate_limiter()
    limiter.ensure_within_limit(
        limit_keys,
        settings.password_change_rate_limit_attempts,
        settings.password_change_rate_limit_window_seconds,
        "Слишком много попыток смены пароля. Повторите позже.",
    )

    try:
        service.change_password(
            user=user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except HTTPException as exc:
        limiter.record_failure(limit_keys, settings.password_change_rate_limit_window_seconds)
        audit.record(
            action="auth.change_password",
            actor=user,
            request=request,
            status="FAILURE",
            details={"username": user.username, "status_code": exc.status_code},
        )
        raise

    limiter.reset(limit_keys)
    service.refresh_session(request, user)
    audit.record(
        action="auth.change_password",
        actor=user,
        request=request,
        status="SUCCESS",
        details={"username": user.username},
    )
    return MessageResponse(message="Пароль успешно обновлён.")
