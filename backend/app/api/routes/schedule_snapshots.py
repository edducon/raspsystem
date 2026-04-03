from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.schedule_snapshot import ScheduleSnapshotCreate, ScheduleSnapshotRead
from app.services.schedule_snapshot_service import ScheduleSnapshotService

router = APIRouter(prefix="/schedule-snapshots", tags=["schedule-snapshots"])


@router.get("/", response_model=list[ScheduleSnapshotRead])
def list_snapshots(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ScheduleSnapshotRead]:
    service = ScheduleSnapshotService(db)
    return service.list_snapshots()


@router.get("/{snapshot_id}", response_model=ScheduleSnapshotRead)
def get_snapshot(
    snapshot_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ScheduleSnapshotRead:
    service = ScheduleSnapshotService(db)
    return service.get_snapshot(snapshot_id)


@router.post("/", response_model=ScheduleSnapshotRead, status_code=status.HTTP_201_CREATED)
def create_snapshot(
    data: ScheduleSnapshotCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ScheduleSnapshotRead:
    service = ScheduleSnapshotService(db)
    return service.create_snapshot(data)


@router.put("/{snapshot_id}", response_model=ScheduleSnapshotRead)
def update_snapshot(
    snapshot_id: int,
    data: ScheduleSnapshotCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ScheduleSnapshotRead:
    service = ScheduleSnapshotService(db)
    return service.update_snapshot(snapshot_id, data)


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(
    snapshot_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = ScheduleSnapshotService(db)
    service.delete_snapshot(snapshot_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
