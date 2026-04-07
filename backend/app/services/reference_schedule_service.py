from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ScheduleSnapshot


class ReferenceScheduleService:
    WEEKDAY_NAMES = {
        1: "monday",
        2: "tuesday",
        3: "wednesday",
        4: "thursday",
        5: "friday",
        6: "saturday",
        7: "sunday",
    }

    def __init__(self, db: Session) -> None:
        self.db = db
        self._sentinel = object()
        self._reference_snapshot: ScheduleSnapshot | None | object = self._sentinel

    def get_reference_snapshot(self) -> ScheduleSnapshot | None:
        if self._reference_snapshot is self._sentinel:
            self._reference_snapshot = self.db.scalar(
                select(ScheduleSnapshot)
                .where(ScheduleSnapshot.is_reference_for_retakes.is_(True))
                .order_by(ScheduleSnapshot.captured_at.desc(), ScheduleSnapshot.id.desc())
            )
        return self._reference_snapshot if isinstance(self._reference_snapshot, ScheduleSnapshot) else None

    def has_reference_snapshot(self) -> bool:
        return self.get_reference_snapshot() is not None

    def list_groups(self) -> list[dict]:
        snapshot = self.get_reference_snapshot()
        return list(snapshot.groups or []) if snapshot is not None else []

    def list_subjects(self) -> list[dict]:
        snapshot = self.get_reference_snapshot()
        return list(snapshot.subjects or []) if snapshot is not None else []

    def list_teachers(self) -> list[dict]:
        snapshot = self.get_reference_snapshot()
        return list(snapshot.teachers or []) if snapshot is not None else []

    def list_schedule_items(self) -> list[dict]:
        snapshot = self.get_reference_snapshot()
        return list(snapshot.schedule_items or []) if snapshot is not None else []

    def find_subject_name(self, subject_uuid: str) -> str | None:
        for subject in self.list_subjects():
            if str(subject.get("uuid")) == subject_uuid:
                return str(subject.get("name") or "")
        return None

    def get_group_subjects(self, group_uuid: str) -> list[dict]:
        subject_map = {
            str(subject.get("uuid") or ""): subject
            for subject in self.list_subjects()
            if subject.get("uuid")
        }
        result: dict[str, dict] = {}
        for item in self.list_schedule_items():
            if str(item.get("group_uuid") or "") != group_uuid:
                continue
            subject_uuid = str(item.get("subject_uuid") or "")
            subject = subject_map.get(subject_uuid)
            if subject is None or subject_uuid in result:
                continue
            result[subject_uuid] = {
                "uuid": subject_uuid,
                "name": str(subject.get("name") or ""),
            }
        return sorted(result.values(), key=lambda item: item["name"])

    def get_group_subject_teacher_names(self, group_uuid: str, subject_uuid: str) -> list[str]:
        teacher_map = {
            str(teacher.get("uuid") or ""): str(teacher.get("full_name") or "")
            for teacher in self.list_teachers()
            if teacher.get("uuid")
        }
        names: set[str] = set()
        for item in self.list_schedule_items():
            if str(item.get("group_uuid") or "") != group_uuid:
                continue
            if str(item.get("subject_uuid") or "") != subject_uuid:
                continue
            for teacher_uuid in item.get("teacher_uuids") or []:
                full_name = teacher_map.get(str(teacher_uuid))
                if full_name:
                    names.add(full_name)
        return sorted(names)

    def build_group_schedule_root(self, group_number: str) -> dict[str, dict[str, list[dict]]]:
        snapshot = self.get_reference_snapshot()
        if snapshot is None:
            return {}

        group_uuids = {
            str(group.get("uuid"))
            for group in (snapshot.groups or [])
            if self._extract_group_number(group) == group_number
        }
        if not group_uuids:
            return {}

        return self._build_schedule_root(
            snapshot=snapshot,
            schedule_items=[
                item
                for item in (snapshot.schedule_items or [])
                if str(item.get("group_uuid") or "") in group_uuids
            ],
        )

    def build_teacher_schedule_root(self, teacher_full_name: str) -> dict[str, dict[str, list[dict]]]:
        snapshot = self.get_reference_snapshot()
        if snapshot is None:
            return {}

        target_name = teacher_full_name.strip().casefold()
        teacher_uuids = {
            str(teacher.get("uuid"))
            for teacher in (snapshot.teachers or [])
            if str(teacher.get("full_name") or "").strip().casefold() == target_name
        }
        if not teacher_uuids:
            return {}

        return self._build_schedule_root(
            snapshot=snapshot,
            schedule_items=[
                item
                for item in (snapshot.schedule_items or [])
                if teacher_uuids.intersection(set(item.get("teacher_uuids") or []))
            ],
        )

    def _build_schedule_root(self, snapshot: ScheduleSnapshot, schedule_items: list[dict]) -> dict[str, dict[str, list[dict]]]:
        groups_by_uuid = {
            str(group.get("uuid")): group
            for group in (snapshot.groups or [])
            if group.get("uuid")
        }
        subjects_by_uuid = {
            str(subject.get("uuid")): subject
            for subject in (snapshot.subjects or [])
            if subject.get("uuid")
        }
        teachers_by_uuid = {
            str(teacher.get("uuid")): teacher
            for teacher in (snapshot.teachers or [])
            if teacher.get("uuid")
        }

        root: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        ordered_items = sorted(
            schedule_items,
            key=lambda item: (
                int(item.get("weekday") or 99),
                int(item.get("slot") or 99),
                str(item.get("group_uuid") or ""),
                str(item.get("subject_uuid") or ""),
            ),
        )

        for item in ordered_items:
            weekday_name = self.WEEKDAY_NAMES.get(int(item.get("weekday") or 0))
            slot_key = str(item.get("slot") or "")
            if weekday_name is None or not slot_key:
                continue

            subject = subjects_by_uuid.get(str(item.get("subject_uuid") or ""), {})
            group = groups_by_uuid.get(str(item.get("group_uuid") or ""), {})
            teacher_payload = [
                {
                    "uuid": teacher_uuid,
                    "full_name": str(teachers_by_uuid.get(teacher_uuid, {}).get("full_name") or ""),
                }
                for teacher_uuid in item.get("teacher_uuids") or []
            ]

            room_value = str(item.get("room") or "").strip()
            root[weekday_name][slot_key].append(
                {
                    "subject": {
                        "uuid": str(subject.get("uuid") or ""),
                        "name": str(subject.get("name") or "Предмет не указан"),
                    },
                    "group": {
                        "uuid": str(group.get("uuid") or ""),
                        "number": self._extract_group_number(group),
                        "name": str(group.get("name") or ""),
                    },
                    "subject_type": {
                        "type": str(item.get("subject_type") or "Не указано"),
                    },
                    "location": {
                        "name": str(item.get("location") or ""),
                    },
                    "rooms": [{"number": room_value}] if room_value else [],
                    "link": item.get("link"),
                    "start_date": item.get("start_date"),
                    "end_date": item.get("end_date"),
                    "teachers": teacher_payload,
                }
            )

        return {
            weekday: {slot: list(items) for slot, items in slots.items()}
            for weekday, slots in root.items()
        }

    def _extract_group_number(self, group: object) -> str:
        if not isinstance(group, dict):
            return ""

        for key in ("number", "group_number", "name"):
            candidate = str(group.get(key) or "").strip()
            if candidate:
                return candidate
        return ""
