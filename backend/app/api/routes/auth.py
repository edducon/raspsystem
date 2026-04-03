from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    AuthChangePasswordRequest,
    AuthLoginRequest,
    AuthResponse,
    AuthUserRead,
    MessageResponse,
)
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
            "department_id": user.department_id,
            "department_ids": list(user.department_ids or []),
            "teacher_uuid": user.teacher_uuid,
        }
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: AuthLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthResponse:
    service = AuthService(db)
    user = service.login(request=request, username=payload.username, password=payload.password)
    return AuthResponse(user=_serialize_user(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: Session = Depends(get_db)) -> Response:
    service = AuthService(db)
    service.logout(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AuthUserRead)
def me(request: Request, db: Session = Depends(get_db)) -> AuthUserRead:
    service = AuthService(db)
    user = service.get_current_user(request)
    return _serialize_user(user)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: AuthChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> MessageResponse:
    service = AuthService(db)
    user = service.get_current_user(request)
    service.change_password(
        user=user,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return MessageResponse(message="Пароль успешно обновлён.")
