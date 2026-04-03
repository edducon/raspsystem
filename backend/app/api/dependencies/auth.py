from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.auth_service import AuthService


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    return AuthService(db).get_current_user(request)


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
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
            detail="Inactive user",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return current_user


def require_scheduler_roles(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role not in {"ADMIN", "EMPLOYEE"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Scheduler access required",
        )
    return current_user
