from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.department import Department


class DepartmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Department]:
        return list(self.db.scalars(select(Department).order_by(Department.name)).all())
