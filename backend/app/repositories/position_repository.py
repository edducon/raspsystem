from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.position import Position
from app.schemas.position import PositionCreate


class PositionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Position]:
        return list(self.db.scalars(select(Position).order_by(Position.sort_order, Position.name)).all())

    def get_by_id(self, position_id: int) -> Position | None:
        return self.db.get(Position, position_id)

    def get_by_name(self, name: str) -> Position | None:
        return self.db.scalar(select(Position).where(Position.name == name))

    def create(self, data: PositionCreate) -> Position:
        position = Position(
            name=data.name,
            sort_order=data.sort_order,
            is_active=data.is_active,
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def update(self, position: Position, data: PositionCreate) -> Position:
        position.name = data.name
        position.sort_order = data.sort_order
        position.is_active = data.is_active
        self.db.commit()
        self.db.refresh(position)
        return position

    def delete(self, position: Position) -> None:
        self.db.delete(position)
        self.db.commit()