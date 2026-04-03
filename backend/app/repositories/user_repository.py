from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.full_name)).all())
