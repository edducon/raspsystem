from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TeacherLocal


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
                detail="Teacher directory entry not found",
            )
        return teacher
