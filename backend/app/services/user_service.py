from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Department, User
from app.schemas.user import UserCreate


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_users(self):
        return list(self.db.scalars(select(User).order_by(User.full_name)).all())

    def get_user(self, user_id: int):
        user = self.db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def create_user(self, data: UserCreate):
        existing = self.db.scalar(select(User).where(User.email == str(data.email)))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        if data.department_id is not None and self.db.get(Department, data.department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

        user = User(
            full_name=data.full_name,
            email=str(data.email),
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=data.is_active,
            department_id=data.department_id,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, data: UserCreate):
        user = self.get_user(user_id)

        existing = self.db.scalar(select(User).where(User.email == str(data.email)))
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )

        if data.department_id is not None and self.db.get(Department, data.department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

        user.full_name = data.full_name
        user.email = str(data.email)
        user.role = data.role
        user.is_active = data.is_active
        user.department_id = data.department_id
        user.password_hash = hash_password(data.password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> None:
        user = self.get_user(user_id)
        self.db.delete(user)
        self.db.commit()
