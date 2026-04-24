import secrets
from datetime import timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jwt import create_access_token, create_refresh_token, create_service_token, verify_token
from app.core.security import hash_password, verify_password
from app.models import User


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def authenticate(self, username: str, password: str) -> User:
        user = self.db.scalar(select(User).where(User.username == username))
        if user is None or not user.is_active or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный логин или пароль.",
            )
        return user

    def get_current_user(self, request: Request) -> User:
        bearer_token = self._get_bearer_token(request)
        if bearer_token:
            return self._get_current_user_from_bearer_token(bearer_token)
        return self._get_current_user_from_session(request)

    def issue_token_pair(self, username: str, password: str) -> dict[str, object]:
        user = self.authenticate(username=username, password=password)
        access_lifetime = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        refresh_lifetime = timedelta(days=settings.jwt_refresh_token_expire_days)
        return {
            "access_token": create_access_token(
                user_id=user.id,
                role=user.role,
                flags=self._schedule_flags(user),
                expires_delta=access_lifetime,
            ),
            "refresh_token": create_refresh_token(user_id=user.id, expires_delta=refresh_lifetime),
            "expires_in": int(access_lifetime.total_seconds()),
            "user": user,
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, object]:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )

        user = self._get_active_user_by_id(payload.get("sub"))
        access_lifetime = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        return {
            "access_token": create_access_token(
                user_id=user.id,
                role=user.role,
                flags=self._schedule_flags(user),
                expires_delta=access_lifetime,
            ),
            "expires_in": int(access_lifetime.total_seconds()),
            "user": user,
        }

    def create_service_token_for_user(self, user_id: int) -> dict[str, object]:
        user = self._get_active_user_by_id(user_id)
        if user.role != "SERVICE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Service token can only be issued for SERVICE accounts.",
            )

        service_lifetime = timedelta(days=365)
        return {
            "access_token": create_service_token(
                user_id=user.id,
                role=user.role,
                flags=self._schedule_flags(user),
                expires_delta=service_lifetime,
            ),
            "expires_in": int(service_lifetime.total_seconds()),
            "user": user,
        }

    def authenticate_access_token(self, token: str) -> User:
        payload = verify_token(token)
        if payload.get("type") not in {"access", "service"}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type.",
            )
        return self._get_active_user_by_id(payload.get("sub"))

    def _get_current_user_from_session(self, request: Request) -> User:
        user_id = request.session.get("user_id")
        session_version = request.session.get("session_version")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется авторизация.",
            )

        user = self.db.get(User, user_id)
        if user is None or not user.is_active:
            request.session.clear()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Требуется авторизация.",
            )

        if session_version != user.session_version:
            request.session.clear()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия была обновлена. Войдите повторно.",
            )

        if not request.session.get("csrf_token"):
            request.session["csrf_token"] = self.issue_csrf_token()

        return user

    def login(self, request: Request, username: str, password: str) -> User:
        user = self.authenticate(username=username, password=password)
        request.session.clear()
        request.session["user_id"] = user.id
        request.session["session_version"] = user.session_version
        request.session["csrf_token"] = self.issue_csrf_token()
        return user

    def logout(self, request: Request) -> None:
        request.session.clear()

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Текущий пароль указан неверно.",
            )

        user.password_hash = hash_password(new_password)
        user.session_version += 1
        user.must_change_password = False
        self.db.add(user)
        self.db.commit()

    def refresh_session(self, request: Request, user: User) -> str:
        token = str(request.session.get("csrf_token") or self.issue_csrf_token())
        request.session["user_id"] = user.id
        request.session["session_version"] = user.session_version
        request.session["csrf_token"] = token
        return token

    def get_csrf_token(self, request: Request) -> str:
        token = request.session.get("csrf_token")
        if token:
            return str(token)
        token = self.issue_csrf_token()
        request.session["csrf_token"] = token
        return token

    @staticmethod
    def issue_csrf_token() -> str:
        return secrets.token_urlsafe(32)

    def _get_current_user_from_bearer_token(self, token: str) -> User:
        return self.authenticate_access_token(token)

    def _get_active_user_by_id(self, user_id: object) -> User:
        try:
            normalized_user_id = int(user_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject.",
            ) from None

        user = self.db.get(User, normalized_user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        return user

    def _get_bearer_token(self, request: Request) -> str | None:
        authorization = request.headers.get("Authorization", "").strip()
        if not authorization:
            return None
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header.",
            )
        return token.strip()

    @staticmethod
    def _schedule_flags(user: User) -> dict[str, bool]:
        return {
            "can_schedule_semester": bool(user.can_schedule_semester),
            "can_schedule_session": bool(user.can_schedule_session),
            "can_schedule_retakes": bool(user.can_schedule_retakes),
        }
