from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import Position


class PositionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Position]:
        return list(self.db.scalars(select(Position).order_by(Position.sort_order, Position.name)).all())
