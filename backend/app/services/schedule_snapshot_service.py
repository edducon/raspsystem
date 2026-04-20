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
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.raspyx_service import RaspyxService


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

        # 1. Скачиваем данные из Go
        schedule_payload = raspyx.get_all_schedule(is_session=False)

        raw_items = schedule_payload.get("result") or schedule_payload.get("response") or []
        if not isinstance(raw_items, list):
            raw_items = schedule_payload if isinstance(schedule_payload, list) else []

        if not raw_items or len(raw_items) < 100:
            print(f"[Sync] Получено пустое или неполное расписание ({len(raw_items)} пар). Отмена сохранения.")
            return None

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

            schedule_items.append({
                "start_date": sem_start,
                "end_date": sem_end,
                "weekday": int(item.get("weekday") or 1),
                "slot": slot,
                "group_uuid": group_uuid,
                "subject_uuid": subj_uuid,
                "teacher_uuids": teacher_uuids,
                "room": room_str
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