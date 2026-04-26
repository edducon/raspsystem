from __future__ import annotations

import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ScheduleSnapshot
from app.schemas.schedule_snapshot import (
    ScheduleSnapshotCreate,
    ScheduleSnapshotListRead,
    ScheduleSnapshotRead,
)
from app.services.raspyx_service import RaspyxService


DATE_VALUE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RASPYX_GROUP_SYNC_WORKERS = 10
RASPYX_GROUP_SYNC_BATCH_SIZE = 25
RASPYX_GROUP_SYNC_BATCH_PAUSE_SECONDS = 1.0
WEEKDAY_KEY_TO_NUMBER = {
    "monday": 1,
    "mon": 1,
    "понедельник": 1,
    "tuesday": 2,
    "tue": 2,
    "вторник": 2,
    "wednesday": 3,
    "wed": 3,
    "среда": 3,
    "thursday": 4,
    "thu": 4,
    "четверг": 4,
    "friday": 5,
    "fri": 5,
    "пятница": 5,
    "saturday": 6,
    "sat": 6,
    "суббота": 6,
    "sunday": 7,
    "sun": 7,
    "воскресенье": 7,
}


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
        snapshot_count = self.db.scalar(select(func.count(ScheduleSnapshot.id)))
        if snapshot.is_reference_for_retakes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить активный снимок расписания.",
            )
        if snapshot_count is not None and snapshot_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить единственный снимок расписания.",
            )
        self.db.delete(snapshot)
        self.db.commit()

    def export_json(self, snapshot_id: int) -> str:
        snapshot = self._get_snapshot_model(snapshot_id)
        payload = self._serialize_detail(snapshot).model_dump(mode="json", by_alias=True)
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def export_csv(self, snapshot_id: int) -> str:
        snapshot = self._get_snapshot_model(snapshot_id)
        groups = {str(item.get("uuid") or ""): item for item in snapshot.groups or []}
        subjects = {str(item.get("uuid") or ""): item for item in snapshot.subjects or []}
        teachers = {str(item.get("uuid") or ""): item for item in snapshot.teachers or []}

        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "snapshot_id",
                "snapshot_name",
                "semester_label",
                "captured_at",
                "group_uuid",
                "group_number",
                "subject_uuid",
                "subject_name",
                "teacher_uuids",
                "teacher_names",
                "weekday",
                "slot",
                "subject_type",
                "location",
                "room",
                "link",
                "start_date",
                "end_date",
            ],
            extrasaction="ignore",
        )
        writer.writeheader()

        for item in snapshot.schedule_items or []:
            group_uuid = str(item.get("group_uuid") or "")
            subject_uuid = str(item.get("subject_uuid") or "")
            teacher_uuids = [str(uuid) for uuid in (item.get("teacher_uuids") or []) if uuid]
            writer.writerow(
                {
                    "snapshot_id": snapshot.id,
                    "snapshot_name": snapshot.name,
                    "semester_label": snapshot.semester_label,
                    "captured_at": snapshot.captured_at.isoformat() if snapshot.captured_at else "",
                    "group_uuid": group_uuid,
                    "group_number": str(groups.get(group_uuid, {}).get("number") or ""),
                    "subject_uuid": subject_uuid,
                    "subject_name": str(subjects.get(subject_uuid, {}).get("name") or ""),
                    "teacher_uuids": "; ".join(teacher_uuids),
                    "teacher_names": "; ".join(str(teachers.get(uuid, {}).get("full_name") or "") for uuid in teacher_uuids),
                    "weekday": item.get("weekday") or "",
                    "slot": item.get("slot") or "",
                    "subject_type": item.get("subject_type") or "",
                    "location": item.get("location") or "",
                    "room": item.get("room") or "",
                    "link": item.get("link") or "",
                    "start_date": item.get("start_date") or "",
                    "end_date": item.get("end_date") or "",
                }
            )

        return output.getvalue()

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

    def activate_latest_as_reference(self) -> None:
        """Находит самый последний скачанный снимок и делает его эталоном (вызывается 1 февраля и 1 сентября)"""
        latest_snapshot = self.db.scalar(
            select(ScheduleSnapshot).order_by(ScheduleSnapshot.created_at.desc()).limit(1)
        )
        if latest_snapshot:
            self._clear_reference_flag(exclude_snapshot_id=None)
            latest_snapshot.is_reference_for_retakes = True
            latest_snapshot.status = "active"
            self.db.commit()
            print(
                f"[Service] Снимок ID {latest_snapshot.id} ({latest_snapshot.semester_label}) успешно назначен эталоном!")

    def _extract_payload_items(self, payload: object) -> list:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []
        for key in ("result", "response", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        return []

    def _group_number_from_payload(self, group: dict) -> str:
        return str(group.get("number") or group.get("name") or group.get("title") or "").strip()

    def _group_uuid_from_payload(self, group: dict, group_number: str) -> str:
        return str(group.get("uuid") or group.get("id") or group_number).strip()

    def _schedule_root_from_payload(self, payload: object) -> dict:
        if not isinstance(payload, dict):
            return {}
        result = payload.get("result") or payload.get("response") or payload.get("data") or {}
        return result if isinstance(result, dict) else {}

    def _weekday_number_from_key(self, key: object) -> int | None:
        key_str = str(key or "").strip()
        if not key_str:
            return None
        if key_str.isdigit():
            number = int(key_str)
            return number if 1 <= number <= 7 else None
        if DATE_VALUE_RE.fullmatch(key_str):
            return datetime.fromisoformat(key_str).isoweekday()
        return WEEKDAY_KEY_TO_NUMBER.get(key_str.casefold())

    def _slot_number_from_key(self, key: object) -> int | None:
        key_str = str(key or "").strip()
        if not key_str:
            return None
        if key_str.isdigit():
            number = int(key_str)
            return number if 1 <= number <= 7 else None
        for number, start_time in (
            (1, "09:00"),
            (2, "10:40"),
            (3, "12:20"),
            (4, "14:30"),
            (5, "16:10"),
            (6, "17:50"),
            (7, "19:30"),
        ):
            if start_time in key_str:
                return number
        return None

    def _flatten_schedule_root(self, schedule_root: dict, group_uuid: str, group_number: str) -> list[dict]:
        items: list[dict] = []
        for day_key, day_schedule in schedule_root.items():
            if not isinstance(day_schedule, dict):
                continue
            weekday = self._weekday_number_from_key(day_key)
            if weekday is None:
                continue

            for slot_key, pairs in day_schedule.items():
                if not isinstance(pairs, list):
                    continue
                slot = self._slot_number_from_key(slot_key)
                if slot is None:
                    continue

                for pair in pairs:
                    if not isinstance(pair, dict):
                        continue
                    normalized_pair = dict(pair)
                    if not isinstance(normalized_pair.get("group"), dict):
                        normalized_pair["group"] = {"uuid": group_uuid, "number": group_number}
                    normalized_pair["weekday"] = normalized_pair.get("weekday") or weekday
                    normalized_pair["slot"] = normalized_pair.get("slot") or slot
                    items.append(normalized_pair)
        return items

    def _load_schedule_items_from_groups(self, raspyx: RaspyxService) -> list[dict]:
        groups = [item for item in self._extract_payload_items(raspyx.get_groups()) if isinstance(item, dict)]
        if not groups:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Raspyx не вернул список групп для загрузки снимка расписания.",
            )

        def load_group_schedule(group: dict) -> list[dict]:
            group_number = self._group_number_from_payload(group)
            if not group_number:
                return []
            group_uuid = self._group_uuid_from_payload(group, group_number)
            payload = None
            for attempt in range(1, 4):
                try:
                    payload = raspyx.get_group_schedule(group_number, is_session=False)
                    break
                except Exception as exc:
                    if attempt >= 3:
                        print(f"[Sync] Не удалось загрузить расписание группы {group_number}: {exc}")
                        return []
                    time.sleep(1.5 * attempt)

            if payload is None:
                return []

            if isinstance(payload, dict) and payload.get("success") is False:
                return []

            flat_items = [
                item
                for item in self._extract_payload_items(payload)
                if isinstance(item, dict)
            ]
            if flat_items:
                for item in flat_items:
                    if not isinstance(item.get("group"), dict):
                        item["group"] = {"uuid": group_uuid, "number": group_number}
                return flat_items

            return self._flatten_schedule_root(
                self._schedule_root_from_payload(payload),
                group_uuid=group_uuid,
                group_number=group_number,
            )

        raw_items: list[dict] = []
        total_groups = len(groups)
        for batch_start in range(0, total_groups, RASPYX_GROUP_SYNC_BATCH_SIZE):
            batch = groups[batch_start:batch_start + RASPYX_GROUP_SYNC_BATCH_SIZE]
            with ThreadPoolExecutor(max_workers=min(RASPYX_GROUP_SYNC_WORKERS, len(batch))) as executor:
                futures = [executor.submit(load_group_schedule, group) for group in batch]
                for future in as_completed(futures):
                    raw_items.extend(future.result())

            processed = min(batch_start + len(batch), total_groups)
            print(f"[Sync] Загружено расписание групп: {processed}/{total_groups}")
            if processed < total_groups:
                time.sleep(RASPYX_GROUP_SYNC_BATCH_PAUSE_SECONDS)

        return raw_items

    def sync_from_raspyx(self) -> ScheduleSnapshotRead | None:
        now = datetime.now(UTC)
        # Определяем, какой семестр сейчас идет по календарю
        if 2 <= now.month <= 7:
            sem_start = f"{now.year}-02-09"
            sem_end = f"{now.year}-07-15"
            sem_label = f"Весенний семестр {now.year}"
        else:
            start_year = now.year if now.month >= 8 else now.year - 1
            sem_start = f"{start_year}-09-01"
            sem_end = f"{start_year + 1}-01-31"
            sem_label = f"Осенний семестр {start_year}/{start_year + 1}"

        raspyx = RaspyxService()

        # 1. Скачиваем данные из Go. Если общий endpoint недоступен, собираем снимок по группам.
        try:
            schedule_payload = raspyx.get_all_schedule(is_session=False)
            raw_items = self._extract_payload_items(schedule_payload)
        except RuntimeError as exc:
            if "failed with 404" not in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Raspyx не отдал расписание: {exc}",
                ) from exc
            print("[Sync] /schedule/all недоступен, загружаем расписание по группам.")
            raw_items = self._load_schedule_items_from_groups(raspyx)

        if not raw_items or len(raw_items) < 100:
            print(f"[Sync] Получено пустое или неполное расписание ({len(raw_items)} пар). Отмена сохранения.")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Raspyx вернул пустое или неполное расписание. Снимок не сохранён.",
            )

        groups_map, subjects_map, teachers_map, schedule_items = {}, {}, {}, []

        # 2. Собираем данные (цикл парсинга)
        for item in raw_items:
            if not isinstance(item, dict): continue

            group_data = item.get("group") or {}
            group_num = str(group_data.get("number") or "").strip()
            group_uuid = str(group_data.get("uuid") or group_num).strip()
            if group_uuid and group_uuid not in groups_map:
                groups_map[group_uuid] = {"uuid": group_uuid, "number": group_num}

            subj_data = item.get("subject") or {}
            subj_name = str(subj_data.get("name") or "").strip()
            subj_uuid = str(subj_data.get("uuid") or subj_name).strip()
            if subj_uuid and subj_uuid not in subjects_map:
                subjects_map[subj_uuid] = {"uuid": subj_uuid, "name": subj_name}

            teacher_uuids = []
            for t in (item.get("teachers") or []):
                t_name = str(t.get("full_name") or "").strip()
                t_uuid = str(t.get("uuid") or t_name).strip()
                if t_uuid and t_uuid not in teachers_map:
                    teachers_map[t_uuid] = {"uuid": t_uuid, "full_name": t_name}
                teacher_uuids.append(t_uuid)

            rooms_data = item.get("rooms") or []
            room_str = ", ".join([str(r.get("number") or "") for r in rooms_data if r.get("number")])

            slot = self._slot_number_from_key(item.get("slot"))
            if slot is None:
                start_time_str = str(item.get("start_time") or "")
                slot = 1
                if "09:00" in start_time_str:
                    slot = 1
                elif "10:40" in start_time_str:
                    slot = 2
                elif "12:20" in start_time_str:
                    slot = 3
                elif "14:30" in start_time_str:
                    slot = 4
                elif "16:10" in start_time_str:
                    slot = 5
                elif "17:50" in start_time_str:
                    slot = 6
                elif "19:30" in start_time_str:
                    slot = 7

            weekday = self._weekday_number_from_key(item.get("weekday")) or 1
            subject_type = item.get("subject_type")
            subject_type_value = (
                str(subject_type.get("type") or subject_type.get("name") or "").strip()
                if isinstance(subject_type, dict)
                else str(subject_type or "").strip()
            )
            location = item.get("location")
            location_value = (
                str(location.get("name") or location.get("title") or "").strip()
                if isinstance(location, dict)
                else str(location or "").strip()
            )

            schedule_items.append({
                "start_date": sem_start,
                "end_date": sem_end,
                "weekday": weekday,
                "slot": slot,
                "group_uuid": group_uuid,
                "subject_uuid": subj_uuid,
                "teacher_uuids": teacher_uuids,
                "subject_type": subject_type_value or None,
                "location": location_value or None,
                "room": room_str,
                "link": item.get("link"),
            })

        # 3. БЕЗОПАСНАЯ ЛОГИКА ЭТАЛОНА
        # Ищем, есть ли в базе уже хоть какой-то эталон
        current_reference = self.db.scalar(
            select(ScheduleSnapshot).where(ScheduleSnapshot.is_reference_for_retakes.is_(True))
        )

        # Если эталона вообще нет (самый первый запуск системы), разрешаем сделать этот снимок эталоном
        is_first_launch = current_reference is None

        now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
        snapshot_data = ScheduleSnapshotCreate(
            name=f"Синхронизация от {now_str}",
            semester_label=sem_label,
            status="active" if is_first_launch else "archived",
            source_type="raspyx",
            is_reference_for_retakes=is_first_launch,  # Истина ТОЛЬКО при холодном старте
            groups=list(groups_map.values()),
            subjects=list(subjects_map.values()),
            teachers=list(teachers_map.values()),
            schedule_items=schedule_items
        )

        # 4. Сохраняем данные (не трогая чужие эталоны)
        if is_first_launch:
            print(f"[Sync] Холодный старт! Создаем первый в истории эталон: {sem_label}")
            return self.create_snapshot(snapshot_data)
        else:
            # Ищем, есть ли уже архивный снимок ТЕКУЩЕГО скачиваемого семестра
            existing_archived = self.db.scalar(
                select(ScheduleSnapshot)
                .where(
                    ScheduleSnapshot.semester_label == sem_label,
                    ScheduleSnapshot.is_reference_for_retakes.is_(False)
                )
                .order_by(ScheduleSnapshot.created_at.desc())
                .limit(1)
            )

            if existing_archived:
                print(f"[Sync] Обновляем фоновый архивный снимок (ID: {existing_archived.id})")
                return self.update_snapshot(existing_archived.id, snapshot_data)
            else:
                print(f"[Sync] Создаем новый фоновый архивный снимок для: {sem_label}")
                return self.create_snapshot(snapshot_data)

    def set_as_reference(self, snapshot_id: int) -> ScheduleSnapshotRead:
        """
        Принудительно назначает указанный снимок эталонным для пересдач.
        Используется для ручного управления через кнопку в админке.
        """
        # 1. Получаем целевой снимок
        snapshot = self._get_snapshot_model(snapshot_id)

        # 2. Снимаем флаг эталона со всех остальных записей в базе
        self._clear_reference_flag(exclude_snapshot_id=snapshot_id)

        # 3. Устанавливаем статус и флаг для выбранного снимка
        snapshot.is_reference_for_retakes = True
        snapshot.status = "active"

        self.db.commit()
        self.db.refresh(snapshot)

        print(f"[Service] Снимок ID {snapshot_id} ({snapshot.semester_label}) назначен эталоном вручную.")
        return self._serialize_detail(snapshot)
