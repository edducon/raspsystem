from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Department
from app.schemas.department import DepartmentCreate


class DepartmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Department]:
        return list(self.db.scalars(select(Department).order_by(Department.name)).all())

    def get_by_id(self, department_id: int) -> Department | None:
        return self.db.get(Department, department_id)

    def get_by_name(self, name: str) -> Department | None:
        return self.db.scalar(select(Department).where(Department.name == name))

    def get_by_short_name(self, short_name: str) -> Department | None:
        return self.db.scalar(select(Department).where(Department.short_name == short_name))

    def create(self, data: DepartmentCreate) -> Department:
        department = Department(name=data.name, short_name=data.short_name)
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        return department

    def update(self, department: Department, data: DepartmentCreate) -> Department:
        department.name = data.name
        department.short_name = data.short_name
        self.db.commit()
        self.db.refresh(department)
        return department

    def delete(self, department: Department) -> None:
        self.db.delete(department)
        self.db.commit()
