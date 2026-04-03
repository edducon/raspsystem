from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Teacher, TeacherLocal, User
from app.repositories.department_repository import DepartmentRepository
from app.schemas.department import DepartmentCreate


class DepartmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DepartmentRepository(db)

    def list_departments(self):
        return self.repository.list_all()

    def get_department(self, department_id: int):
        department = self.repository.get_by_id(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Кафедра не найдена.",
            )
        return department

    def create_department(self, data: DepartmentCreate):
        existing_by_name = self.repository.get_by_name(data.name)
        if existing_by_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Кафедра с таким названием уже существует.",
            )

        existing_by_short_name = self.repository.get_by_short_name(data.short_name)
        if existing_by_short_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Кафедра с таким сокращением уже существует.",
            )

        return self.repository.create(data)

    def update_department(self, department_id: int, data: DepartmentCreate):
        department = self.get_department(department_id)

        existing_by_name = self.repository.get_by_name(data.name)
        if existing_by_name and existing_by_name.id != department_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Кафедра с таким названием уже существует.",
            )

        existing_by_short_name = self.repository.get_by_short_name(data.short_name)
        if existing_by_short_name and existing_by_short_name.id != department_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Кафедра с таким сокращением уже существует.",
            )

        return self.repository.update(department, data)

    def delete_department(self, department_id: int) -> None:
        department = self.get_department(department_id)

        linked_user = self.db.scalar(select(User).where(User.department_id == department_id))
        if linked_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить кафедру: она указана как основная у пользователя.",
            )

        linked_teacher = self.db.scalar(select(Teacher).where(Teacher.department_id == department_id))
        if linked_teacher is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить кафедру: она привязана к преподавателю.",
            )

        linked_user_scope = self.db.scalar(
            select(User.id).where(User.department_ids.contains([department_id]))
        )
        if linked_user_scope is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить кафедру: она используется в областях доступа пользователей.",
            )

        linked_teacher_scope = self.db.scalar(
            select(TeacherLocal.uuid).where(TeacherLocal.department_ids.contains([department_id]))
        )
        if linked_teacher_scope is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Нельзя удалить кафедру: она используется в справочнике преподавателей.",
            )

        self.repository.delete(department)
