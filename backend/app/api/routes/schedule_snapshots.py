from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_admin
from app.db.session import get_db
from app.schemas.schedule_snapshot import ScheduleSnapshotCreate, ScheduleSnapshotListRead, ScheduleSnapshotRead
from app.services.audit_service import AuditService
from app.services.schedule_snapshot_service import ScheduleSnapshotService

router = APIRouter(prefix="/schedule-snapshots", tags=["schedule-snapshots"])


@router.get("/", response_model=list[ScheduleSnapshotListRead])
def list_snapshots(
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[ScheduleSnapshotListRead]:
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
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ScheduleSnapshotRead:
    service = ScheduleSnapshotService(db)
    snapshot = service.create_snapshot(data)
    AuditService(db).record(
        action="admin.schedule_snapshot.create",
        actor=current_admin,
        request=request,
        target_type="schedule_snapshot",
        target_id=str(snapshot.id),
        details={"name": snapshot.name, "semester_label": snapshot.semester_label},
    )
    return snapshot


@router.put("/{snapshot_id}", response_model=ScheduleSnapshotRead)
def update_snapshot(
    snapshot_id: int,
    data: ScheduleSnapshotCreate,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ScheduleSnapshotRead:
    service = ScheduleSnapshotService(db)
    snapshot = service.update_snapshot(snapshot_id, data)
    AuditService(db).record(
        action="admin.schedule_snapshot.update",
        actor=current_admin,
        request=request,
        target_type="schedule_snapshot",
        target_id=str(snapshot.id),
        details={"name": snapshot.name, "semester_label": snapshot.semester_label},
    )
    return snapshot


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot(
    snapshot_id: int,
    request: Request,
    current_admin: object = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    service = ScheduleSnapshotService(db)
    snapshot = service.get_snapshot(snapshot_id)
    service.delete_snapshot(snapshot_id)
    AuditService(db).record(
        action="admin.schedule_snapshot.delete",
        actor=current_admin,
        request=request,
        target_type="schedule_snapshot",
        target_id=str(snapshot_id),
        details={"name": snapshot.name, "semester_label": snapshot.semester_label},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
