import secrets

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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
                detail="РќРµРІРµСЂРЅС‹Р№ Р»РѕРіРёРЅ РёР»Рё РїР°СЂРѕР»СЊ.",
            )
        return user

    def get_current_user(self, request: Request) -> User:
        user_id = request.session.get("user_id")
        session_version = request.session.get("session_version")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="РўСЂРµР±СѓРµС‚СЃСЏ Р°РІС‚РѕСЂРёР·Р°С†РёСЏ.",
            )

        user = self.db.get(User, user_id)
        if user is None or not user.is_active:
            request.session.clear()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="РўСЂРµР±СѓРµС‚СЃСЏ Р°РІС‚РѕСЂРёР·Р°С†РёСЏ.",
            )

        if session_version != user.session_version:
            request.session.clear()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="РЎРµСЃСЃРёСЏ Р±С‹Р»Р° РѕР±РЅРѕРІР»РµРЅР°. Р’РѕР№РґРёС‚Рµ РїРѕРІС‚РѕСЂРЅРѕ.",
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
                detail="РўРµРєСѓС‰РёР№ РїР°СЂРѕР»СЊ СѓРєР°Р·Р°РЅ РЅРµРІРµСЂРЅРѕ.",
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
