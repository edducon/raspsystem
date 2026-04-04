from __future__ import annotations

import re
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ScheduleSnapshot
from app.schemas.schedule_snapshot import (
    ScheduleSnapshotCreate,
    ScheduleSnapshotListRead,
    ScheduleSnapshotRead,
)


DATE_VALUE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ScheduleSnapshotService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_snapshots(self) -> list[ScheduleSnapshotListRead]:
        snapshots = list(
            self.db.scalars(
                select(ScheduleSnapshot).order_by(ScheduleSnapshot.created_at.desc(), ScheduleSnapshot.id.desc())
            ).all()
        )
        return [self._serialize_summary(snapshot) for snapshot in snapshots]

    def get_snapshot(self, snapshot_id: int) -> ScheduleSnapshotRead:
        return self._serialize_detail(self._get_snapshot_model(snapshot_id))

    def create_snapshot(self, data: ScheduleSnapshotCreate) -> ScheduleSnapshotRead:
        normalized_payload = self._normalize_payload(data)

        if data.is_reference_for_retakes:
            self._clear_reference_flag(exclude_snapshot_id=None)

        snapshot = ScheduleSnapshot(
            name=data.name,
            semester_label=data.semester_label,
            status=data.status,
            source_type=data.source_type,
            description=data.description,
            is_reference_for_retakes=data.is_reference_for_retakes,
            captured_at=data.captured_at or datetime.now(UTC),
            groups=normalized_payload["groups"],
            subjects=normalized_payload["subjects"],
            teachers=normalized_payload["teachers"],
            schedule_items=normalized_payload["schedule_items"],
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return self._serialize_detail(snapshot)

    def update_snapshot(self, snapshot_id: int, data: ScheduleSnapshotCreate) -> ScheduleSnapshotRead:
        snapshot = self._get_snapshot_model(snapshot_id)
        normalized_payload = self._normalize_payload(data)

        if data.is_reference_for_retakes:
            self._clear_reference_flag(exclude_snapshot_id=snapshot_id)

        snapshot.name = data.name
        snapshot.semester_label = data.semester_label
        snapshot.status = data.status
        snapshot.source_type = data.source_type
        snapshot.description = data.description
        snapshot.is_reference_for_retakes = data.is_reference_for_retakes
        snapshot.captured_at = data.captured_at or snapshot.captured_at
        snapshot.groups = normalized_payload["groups"]
        snapshot.subjects = normalized_payload["subjects"]
        snapshot.teachers = normalized_payload["teachers"]
        snapshot.schedule_items = normalized_payload["schedule_items"]
        self.db.commit()
        self.db.refresh(snapshot)
        return self._serialize_detail(snapshot)

    def delete_snapshot(self, snapshot_id: int) -> None:
        snapshot = self._get_snapshot_model(snapshot_id)
        self.db.delete(snapshot)
        self.db.commit()

    def _get_snapshot_model(self, snapshot_id: int) -> ScheduleSnapshot:
        snapshot = self.db.get(ScheduleSnapshot, snapshot_id)
        if snapshot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Снимок расписания не найден.",
            )
        return snapshot

    def _clear_reference_flag(self, exclude_snapshot_id: int | None) -> None:
        query = select(ScheduleSnapshot).where(ScheduleSnapshot.is_reference_for_retakes.is_(True))
        if exclude_snapshot_id is not None:
            query = query.where(ScheduleSnapshot.id != exclude_snapshot_id)

        current_reference = self.db.scalar(query)
        if current_reference is not None:
            current_reference.is_reference_for_retakes = False

    def _normalize_payload(self, data: ScheduleSnapshotCreate) -> dict[str, list[dict]]:
        groups = [group.model_dump() for group in data.groups]
        subjects = [subject.model_dump() for subject in data.subjects]
        teachers = [teacher.model_dump() for teacher in data.teachers]
        schedule_items = [item.model_dump() for item in data.schedule_items]

        group_uuid_map = self._unique_map(
            values=groups,
            key_name="uuid",
            duplicate_message="UUID группы в содержимом snapshot должен быть уникальным.",
            empty_message="UUID группы в содержимом snapshot обязателен.",
        )
        self._unique_map(
            values=groups,
            key_name="number",
            duplicate_message="Номер группы в содержимом snapshot должен быть уникальным.",
            empty_message="Номер группы в содержимом snapshot обязателен.",
        )
        subject_uuid_map = self._unique_map(
            values=subjects,
            key_name="uuid",
            duplicate_message="UUID дисциплины в содержимом snapshot должен быть уникальным.",
            empty_message="UUID дисциплины в содержимом snapshot обязателен.",
        )
        teacher_uuid_map = self._unique_map(
            values=teachers,
            key_name="uuid",
            duplicate_message="UUID преподавателя в содержимом snapshot должен быть уникальным.",
            empty_message="UUID преподавателя в содержимом snapshot обязателен.",
        )

        for item in schedule_items:
            group_uuid = str(item.get("group_uuid") or "")
            subject_uuid = str(item.get("subject_uuid") or "")
            if group_uuid not in group_uuid_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Для элемента расписания не найдена группа {group_uuid}.",
                )
            if subject_uuid not in subject_uuid_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Для элемента расписания не найдена дисциплина {subject_uuid}.",
                )

            for teacher_uuid in item.get("teacher_uuids") or []:
                if teacher_uuid not in teacher_uuid_map:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Для элемента расписания не найден преподаватель {teacher_uuid}.",
                    )

        return {
            "groups": groups,
            "subjects": subjects,
            "teachers": teachers,
            "schedule_items": schedule_items,
        }

    def _unique_map(
        self,
        values: list[dict],
        key_name: str,
        duplicate_message: str,
        empty_message: str,
    ) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for value in values:
            key = str(value.get(key_name) or "").strip()
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=empty_message,
                )
            if key in result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=duplicate_message,
                )
            result[key] = value
        return result

    def _serialize_summary(self, snapshot: ScheduleSnapshot) -> ScheduleSnapshotListRead:
        date_range_start, date_range_end = self._extract_date_bounds(snapshot.schedule_items or [])
        return ScheduleSnapshotListRead.model_validate(
            {
                "id": snapshot.id,
                "name": snapshot.name,
                "semester_label": snapshot.semester_label,
                "status": snapshot.status,
                "source_type": snapshot.source_type,
                "description": snapshot.description,
                "is_reference_for_retakes": snapshot.is_reference_for_retakes,
                "captured_at": snapshot.captured_at,
                "created_at": snapshot.created_at,
                "date_range_start": date_range_start,
                "date_range_end": date_range_end,
                "group_count": len(snapshot.groups or []),
                "subject_count": len(snapshot.subjects or []),
                "teacher_count": len(snapshot.teachers or []),
                "schedule_item_count": len(snapshot.schedule_items or []),
            }
        )

    def _serialize_detail(self, snapshot: ScheduleSnapshot) -> ScheduleSnapshotRead:
        return ScheduleSnapshotRead.model_validate(
            {
                "id": snapshot.id,
                "name": snapshot.name,
                "semester_label": snapshot.semester_label,
                "status": snapshot.status,
                "source_type": snapshot.source_type,
                "description": snapshot.description,
                "is_reference_for_retakes": snapshot.is_reference_for_retakes,
                "captured_at": snapshot.captured_at,
                "created_at": snapshot.created_at,
                "groups": snapshot.groups or [],
                "subjects": snapshot.subjects or [],
                "teachers": snapshot.teachers or [],
                "schedule_items": snapshot.schedule_items or [],
                "group_count": len(snapshot.groups or []),
                "subject_count": len(snapshot.subjects or []),
                "teacher_count": len(snapshot.teachers or []),
                "schedule_item_count": len(snapshot.schedule_items or []),
            }
        )

    def _extract_date_bounds(self, schedule_items: list[dict]) -> tuple[str | None, str | None]:
        dates = sorted(self._collect_date_values(schedule_items))
        if not dates:
            return None, None
        return dates[0], dates[-1]

    def _collect_date_values(self, value: object) -> set[str]:
        result: set[str] = set()

        def visit(node: object) -> None:
            if isinstance(node, str):
                normalized = node.strip()
                if DATE_VALUE_RE.fullmatch(normalized):
                    result.add(normalized)
                return

            if isinstance(node, list):
                for item in node:
                    visit(item)
                return

            if not isinstance(node, dict):
                return

            for key, nested in node.items():
                key_str = str(key).strip()
                if DATE_VALUE_RE.fullmatch(key_str):
                    result.add(key_str)
                visit(nested)

        visit(value)
        return result
