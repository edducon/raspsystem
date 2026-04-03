from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Department, RetakeTeacher, TeacherLocal, User
from app.schemas.teacher_directory import TeacherDirectoryCreate, TeacherDirectoryUpdate


class TeacherDirectoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_teachers(self) -> list[TeacherLocal]:
        return list(self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name)).all())

    def get_teacher(self, teacher_uuid: str) -> TeacherLocal:
        teacher = self.db.get(TeacherLocal, teacher_uuid)
        if teacher is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Преподаватель из справочника не найден.",
            )
        return teacher

    def create_teacher(self, data: TeacherDirectoryCreate) -> TeacherLocal:
        department_ids = self._validate_departments(data.department_ids)
        teacher_uuid = str(data.uuid or uuid4())
        if self.db.get(TeacherLocal, teacher_uuid) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Преподаватель с таким UUID уже есть в справочнике.",
            )

        teacher = TeacherLocal(
            uuid=teacher_uuid,
            full_name=data.full_name,
            department_ids=department_ids,
        )
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def update_teacher(self, teacher_uuid: str, data: TeacherDirectoryUpdate) -> TeacherLocal:
        teacher = self.get_teacher(teacher_uuid)
        teacher.full_name = data.full_name
        teacher.department_ids = self._validate_departments(data.department_ids)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def delete_teacher(self, teacher_uuid: str) -> None:
        teacher = self.get_teacher(teacher_uuid)

        linked_user = self.db.scalar(select(User).where(User.teacher_uuid == teacher_uuid))
        if linked_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить преподавателя из справочника: он привязан к пользователю.",
            )

        linked_retake = self.db.scalar(select(RetakeTeacher).where(RetakeTeacher.teacher_uuid == teacher_uuid))
        if linked_retake is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить преподавателя из справочника: он используется в назначенных пересдачах.",
            )

        self.db.delete(teacher)
        self.db.commit()

    def _validate_departments(self, department_ids: list[int]) -> list[int]:
        normalized = list(dict.fromkeys(department_ids))
        if not normalized:
            return []

        existing_ids = set(self.db.scalars(select(Department.id).where(Department.id.in_(normalized))).all())
        missing_ids = [value for value in normalized if value not in existing_ids]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не найдены кафедры: {', '.join(str(value) for value in missing_ids)}.",
            )
        return normalized
