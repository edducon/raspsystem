from datetime import datetime, UTC

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ScheduleSnapshot
from app.schemas.schedule_snapshot import ScheduleSnapshotCreate


class ScheduleSnapshotService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_snapshots(self):
        return list(
            self.db.scalars(
                select(ScheduleSnapshot).order_by(ScheduleSnapshot.created_at.desc(), ScheduleSnapshot.id.desc())
            ).all()
        )

    def get_snapshot(self, snapshot_id: int):
        snapshot = self.db.get(ScheduleSnapshot, snapshot_id)
        if not snapshot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Schedule snapshot not found",
            )
        return snapshot

    def create_snapshot(self, data: ScheduleSnapshotCreate):
        if data.is_reference_for_retakes:
            current_reference = self.db.scalar(
                select(ScheduleSnapshot).where(ScheduleSnapshot.is_reference_for_retakes.is_(True))
            )
            if current_reference is not None:
                current_reference.is_reference_for_retakes = False

        snapshot = ScheduleSnapshot(
            name=data.name,
            semester_label=data.semester_label,
            status=data.status,
            source_type=data.source_type,
            description=data.description,
            is_reference_for_retakes=data.is_reference_for_retakes,
            captured_at=data.captured_at or datetime.now(UTC),
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def update_snapshot(self, snapshot_id: int, data: ScheduleSnapshotCreate):
        snapshot = self.get_snapshot(snapshot_id)

        if data.is_reference_for_retakes:
            current_reference = self.db.scalar(
                select(ScheduleSnapshot).where(
                    ScheduleSnapshot.is_reference_for_retakes.is_(True),
                    ScheduleSnapshot.id != snapshot_id,
                )
            )
            if current_reference is not None:
                current_reference.is_reference_for_retakes = False

        snapshot.name = data.name
        snapshot.semester_label = data.semester_label
        snapshot.status = data.status
        snapshot.source_type = data.source_type
        snapshot.description = data.description
        snapshot.is_reference_for_retakes = data.is_reference_for_retakes
        snapshot.captured_at = data.captured_at or snapshot.captured_at
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def delete_snapshot(self, snapshot_id: int) -> None:
        snapshot = self.get_snapshot(snapshot_id)
        self.db.delete(snapshot)
        self.db.commit()
