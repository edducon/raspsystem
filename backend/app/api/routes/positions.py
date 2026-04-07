from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.position import PositionCreate, PositionRead
from app.services.audit_service import AuditService
from app.services.position_service import PositionService

router = APIRouter(prefix="/positions", tags=["positions"])


@router.get("/", response_model=list[PositionRead])
def list_positions(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[PositionRead]:
    service = PositionService(db)
    return service.list_positions()


@router.get("/{position_id}", response_model=PositionRead)
def get_position(
    position_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PositionRead:
    service = PositionService(db)
    return service.get_position(position_id)


@router.post("/", response_model=PositionRead, status_code=status.HTTP_201_CREATED)
def create_position(
    data: PositionCreate,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PositionRead:
    service = PositionService(db)
    position = service.create_position(data)
    AuditService(db).record(
        action="admin.position.create",
        actor=current_admin,
        request=request,
        target_type="position",
        target_id=str(position.id),
        details={"name": position.name},
    )
    return position


@router.put("/{position_id}", response_model=PositionRead)
def update_position(
    position_id: int,
    data: PositionCreate,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> PositionRead:
    service = PositionService(db)
    position = service.update_position(position_id, data)
    AuditService(db).record(
        action="admin.position.update",
        actor=current_admin,
        request=request,
        target_type="position",
        target_id=str(position.id),
        details={"name": position.name},
    )
    return position


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: int,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = PositionService(db)
    position = service.get_position(position_id)
    service.delete_position(position_id)
    AuditService(db).record(
        action="admin.position.delete",
        actor=current_admin,
        request=request,
        target_type="position",
        target_id=str(position_id),
        details={"name": position.name},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
