from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.position import PositionCreate, PositionRead
from app.services.position_service import PositionService

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=list[PositionRead])
def list_positions(db: Session = Depends(get_db)) -> list[PositionRead]:
    service = PositionService(db)
    return service.list_positions()


@router.get("/{position_id}", response_model=PositionRead)
def get_position(position_id: int, db: Session = Depends(get_db)) -> PositionRead:
    service = PositionService(db)
    return service.get_position(position_id)


@router.post("/", response_model=PositionRead, status_code=status.HTTP_201_CREATED)
def create_position(data: PositionCreate, db: Session = Depends(get_db)) -> PositionRead:
    service = PositionService(db)
    return service.create_position(data)


@router.put("/{position_id}", response_model=PositionRead)
def update_position(
        position_id: int,
        data: PositionCreate,
        db: Session = Depends(get_db),
) -> PositionRead:
    service = PositionService(db)
    return service.update_position(position_id, data)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(position_id: int, db: Session = Depends(get_db)) -> Response:
    service = PositionService(db)
    service.delete_position(position_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)