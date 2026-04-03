from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.teacher import Teacher


class TeacherRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Teacher]:
        return list(self.db.scalars(select(Teacher).order_by(Teacher.full_name)).all())
