from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Department, TeacherLocal, User
from app.schemas.user import UserCreate, UserUpdate


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
                detail="Пользователь не найден.",
            )
        return user

    def create_user(self, data: UserCreate):
        department_ids = self._normalize_department_ids(data.department_id, data.department_ids)
        self._validate_departments(data.department_id, department_ids)
        teacher_uuid = self._validate_teacher_uuid(data.teacher_uuid)
        existing_user = self.db.scalar(select(User).where(User.username == data.username))
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Логин уже занят.",
            )

        user = User(
            username=data.username,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
            role=data.role,
            is_active=data.is_active,
            department_id=data.department_id,
            department_ids=department_ids,
            teacher_uuid=teacher_uuid,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user_id: int, data: UserUpdate, actor: User):
        user = self.get_user(user_id)
        self._ensure_user_update_allowed(user=user, data=data, actor=actor)
        department_ids = self._normalize_department_ids(data.department_id, data.department_ids)
        self._validate_departments(data.department_id, department_ids)
        teacher_uuid = self._validate_teacher_uuid(data.teacher_uuid)
        existing_user = self.db.scalar(
            select(User).where(
                User.username == data.username,
                User.id != user_id,
            )
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Логин уже занят.",
            )

        user.username = data.username
        user.full_name = data.full_name
        user.role = data.role
        user.is_active = data.is_active
        user.department_id = data.department_id
        user.department_ids = department_ids
        user.teacher_uuid = teacher_uuid
        if data.password:
            user.password_hash = hash_password(data.password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int, actor: User) -> None:
        user = self.get_user(user_id)
        self._ensure_user_delete_allowed(user=user, actor=actor)
        self.db.delete(user)
        self.db.commit()

    def _normalize_department_ids(self, department_id: int | None, department_ids: list[int]) -> list[int]:
        normalized = list(dict.fromkeys(department_ids))
        if department_id is not None and department_id not in normalized:
            normalized.append(department_id)
        return normalized

    def _validate_departments(self, department_id: int | None, department_ids: list[int]) -> None:
        requested_ids = list(dict.fromkeys(([department_id] if department_id is not None else []) + department_ids))
        if not requested_ids:
            return

        existing_ids = set(self.db.scalars(select(Department.id).where(Department.id.in_(requested_ids))).all())
        missing_ids = [value for value in requested_ids if value not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не найдены кафедры: {', '.join(str(value) for value in missing_ids)}.",
            )

    def _validate_teacher_uuid(self, teacher_uuid: str | None) -> str | None:
        normalized = teacher_uuid.strip() if teacher_uuid else None
        if not normalized:
            return None

        if self.db.get(TeacherLocal, normalized) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Преподаватель из справочника не найден.",
            )
        return normalized

    def _ensure_user_update_allowed(self, user: User, data: UserUpdate, actor: User) -> None:
        if user.role == "ADMIN" and data.role != "ADMIN":
            if self._count_admins() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Нельзя снять роль ADMIN у последнего администратора.",
                )
            if user.is_active and self._count_active_admins() <= 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Нельзя снять роль ADMIN у последнего активного администратора.",
                )

        if user.role == "ADMIN" and user.is_active and not data.is_active and self._count_active_admins() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя деактивировать последнего активного администратора.",
            )

    def _ensure_user_delete_allowed(self, user: User, actor: User) -> None:
        if user.id == actor.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить собственную учётную запись.",
            )

        if user.role != "ADMIN":
            return

        if self._count_admins() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить последнего администратора.",
            )

        if user.is_active and self._count_active_admins() <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить последнего активного администратора.",
            )

    def _count_admins(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(User).where(User.role == "ADMIN")
            )
            or 0
        )

    def _count_active_admins(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(User).where(
                    User.role == "ADMIN",
                    User.is_active.is_(True),
                )
            )
            or 0
        )
