from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.position_repository import PositionRepository
from app.schemas.position import PositionCreate


class PositionService:
    def __init__(self, db: Session) -> None:
        self.repository = PositionRepository(db)

    def list_positions(self):
        return self.repository.list_all()

    def get_position(self, position_id: int):
        position = self.repository.get_by_id(position_id)
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found",
            )
        return position

    def create_position(self, data: PositionCreate):
        existing = self.repository.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Position with this name already exists",
            )
        return self.repository.create(data)

    def update_position(self, position_id: int, data: PositionCreate):
        position = self.get_position(position_id)

        existing = self.repository.get_by_name(data.name)
        if existing and existing.id != position_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Position with this name already exists",
            )

        return self.repository.update(position, data)

    def delete_position(self, position_id: int) -> None:
        position = self.get_position(position_id)
        self.repository.delete(position)