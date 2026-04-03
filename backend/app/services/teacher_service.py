from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Department, Position, Teacher
from app.schemas.teacher import TeacherCreate


class TeacherService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_teachers(self):
        return list(self.db.scalars(select(Teacher).order_by(Teacher.full_name)).all())

    def get_teacher(self, teacher_id: int):
        teacher = self.db.get(Teacher, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found",
            )
        return teacher

    def create_teacher(self, data: TeacherCreate):
        if self.db.get(Department, data.department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

        if data.position_id is not None and self.db.get(Position, data.position_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position not found",
            )

        if data.email is not None:
            existing = self.db.scalar(select(Teacher).where(Teacher.email == str(data.email)))
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Teacher with this email already exists",
                )

        teacher = Teacher(
            full_name=data.full_name,
            email=str(data.email) if data.email is not None else None,
            department_id=data.department_id,
            position_id=data.position_id,
        )
        self.db.add(teacher)
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def update_teacher(self, teacher_id: int, data: TeacherCreate):
        teacher = self.get_teacher(teacher_id)

        if self.db.get(Department, data.department_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found",
            )

        if data.position_id is not None and self.db.get(Position, data.position_id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position not found",
            )

        if data.email is not None:
            existing = self.db.scalar(select(Teacher).where(Teacher.email == str(data.email)))
            if existing and existing.id != teacher_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Teacher with this email already exists",
                )

        teacher.full_name = data.full_name
        teacher.email = str(data.email) if data.email is not None else None
        teacher.department_id = data.department_id
        teacher.position_id = data.position_id
        self.db.commit()
        self.db.refresh(teacher)
        return teacher

    def delete_teacher(self, teacher_id: int) -> None:
        teacher = self.get_teacher(teacher_id)
        self.db.delete(teacher)
        self.db.commit()
