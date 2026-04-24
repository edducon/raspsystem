from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.auth_service import AuthService


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    return AuthService(db).get_current_user(request)


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    authorization = request.headers.get("Authorization", "").strip()
    if authorization:
        return AuthService(db).get_current_user(request)

    if request.session.get("user_id") is None:
        return None

    try:
        return AuthService(db).get_current_user(request)
    except HTTPException:
        request.session.clear()
        return None


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь деактивирован.",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Требуются права администратора.",
        )
    return current_user


def require_scheduler_roles(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role not in {"ADMIN", "EMPLOYEE"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для работы с расписанием пересдач.",
        )
    return current_user


def require_schedule_semester(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role == "ADMIN" or current_user.can_schedule_semester:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions for semester schedule management.",
    )


def require_schedule_session(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role == "ADMIN" or current_user.can_schedule_session:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions for session schedule management.",
    )


def require_schedule_retakes(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role == "ADMIN" or current_user.can_schedule_retakes:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions for retake schedule management.",
    )
