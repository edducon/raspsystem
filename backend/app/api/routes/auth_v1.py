from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.models import User
from app.schemas.auth import AuthLoginRequest, ServiceTokenRequest, TokenRefreshRequest, TokenResponse
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth-v1"])


@router.post("/token", response_model=TokenResponse)
def issue_token(
    payload: AuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    result = AuthService(db).issue_token_pair(payload.username, payload.password)
    user = result["user"]
    AuditService(db).record(
        action="auth.token",
        actor=user,
        request=request,
        status="SUCCESS",
        details={"username": user.username},
    )
    return TokenResponse(
        access_token=str(result["access_token"]),
        refresh_token=str(result["refresh_token"]),
        expires_in=int(result["expires_in"]),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    payload: TokenRefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenResponse:
    result = AuthService(db).refresh_access_token(payload.refresh_token)
    user = result["user"]
    AuditService(db).record(
        action="auth.refresh",
        actor=user,
        request=request,
        status="SUCCESS",
        details={"username": user.username},
    )
    return TokenResponse(
        access_token=str(result["access_token"]),
        refresh_token=None,
        expires_in=int(result["expires_in"]),
    )


@router.post("/token/service", response_model=TokenResponse)
def issue_service_token(
    payload: ServiceTokenRequest,
    request: Request,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> TokenResponse:
    result = AuthService(db).create_service_token_for_user(payload.user_id)
    service_user = result["user"]
    AuditService(db).record(
        action="auth.token.service",
        actor=current_admin,
        request=request,
        status="SUCCESS",
        target_type="user",
        target_id=str(service_user.id),
        details={"username": service_user.username},
    )
    return TokenResponse(
        access_token=str(result["access_token"]),
        refresh_token=None,
        expires_in=int(result["expires_in"]),
    )
