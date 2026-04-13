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

    def sync_from_raspyx(self) -> ScheduleSnapshotRead:
        # =======================================================
        # 2. УМНЫЙ КАЛЕНДАРЬ: Автоматически вычисляем границы семестра
        # =======================================================
        now = datetime.now(UTC)
        if 2 <= now.month <= 7:
            # С февраля по июль — Весенний семестр
            sem_start = f"{now.year}-02-09"
            sem_end = f"{now.year}-07-15"
            sem_label = f"Весенний семестр {now.year}"
        else:
            # С августа по январь — Осенний семестр
            start_year = now.year if now.month >= 8 else now.year - 1
            sem_start = f"{start_year}-09-01"
            sem_end = f"{start_year + 1}-01-31"
            sem_label = f"Осенний семестр {start_year}/{start_year + 1}"

        raspyx = RaspyxService()

        # 3. Получаем список групп
        groups_payload = raspyx.get_groups()
        raw_groups = groups_payload.get("result") or groups_payload.get("response") or []

        # Собираем словари для JSON (нам нужны UUID и номера групп)
        groups = []
        group_numbers = []
        for g in raw_groups:
            num = str(g.get("number") or g.get("name") or "").strip()
            guid = str(g.get("uuid") or g.get("id") or "").strip()
            if num and guid:
                groups.append({"uuid": guid, "number": num})
                group_numbers.append(num)

        # Словари для уникальных преподавателей и предметов
        subjects_map = {}
        teachers_map = {}
        schedule_items = []

        # 4. Многопоточно скачиваем расписание для всех групп
        max_workers = min(8, len(group_numbers))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(raspyx.get_group_schedule, num): num
                for num in group_numbers
            }

            for future in as_completed(future_to_group):
                group_num = future_to_group[future]
                try:
                    schedule_payload = future.result()
                    raw_schedule = schedule_payload.get("result") or schedule_payload.get("response") or {}

                    # Ищем UUID группы для привязки
                    group_uuid = next((g["uuid"] for g in groups if g["number"] == group_num), None)
                    if not group_uuid:
                        continue

                    # Парсим дни и пары
                    for date_str, day_data in raw_schedule.items():
                        if not isinstance(day_data, dict):
                            continue

                        # По умолчанию назначаем паре рамки всего семестра из умного календаря!
                        actual_start = sem_start
                        actual_end = sem_end
                        weekday = 1

                        # Проверяем, является ли ключ точной датой (ГГГГ-ММ-ДД) или днем недели ("friday")
                        if re.fullmatch(r"^\d{4}-\d{2}-\d{2}$", str(date_str).strip()):
                            try:
                                dt = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
                                weekday = dt.weekday() + 1
                                # Если Raspyx вдруг отдал точную дату (например, экзамен), используем её
                                actual_start = str(date_str).strip()
                                actual_end = str(date_str).strip()
                            except ValueError:
                                pass
                        else:
                            # Если это день недели текстом, превращаем его в цифру
                            weekdays_map = {
                                "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
                                "friday": 5, "saturday": 6, "sunday": 7,
                                "понедельник": 1, "вторник": 2, "среда": 3, "четверг": 4,
                                "пятница": 5, "суббота": 6, "воскресенье": 7
                            }
                            weekday = weekdays_map.get(str(date_str).lower().strip(), 1)

                        for pairs in day_data.values():
                            if not isinstance(pairs, list):
                                continue

                            for pair in pairs:
                                # Извлекаем предмет
                                subj_raw = pair.get("subject", {})
                                subj_name = str(
                                    subj_raw.get("name") or pair.get("subject_name") or "Неизвестно").strip()
                                subj_uuid = str(subj_raw.get("uuid") or subj_name)
                                subjects_map[subj_uuid] = {"uuid": subj_uuid, "name": subj_name}

                                # Извлекаем преподавателей
                                teacher_uuids = []
                                for t in pair.get("teachers") or []:
                                    t_name = str(t.get("full_name") or t.get("fio") or t).strip()
                                    t_uuid = str(t.get("uuid") or t_name)
                                    teachers_map[t_uuid] = {"uuid": t_uuid, "full_name": t_name}
                                    teacher_uuids.append(t_uuid)

                                # Формируем занятие
                                schedule_items.append({
                                    "start_date": actual_start, # <-- Заполняем вычисленными датами!
                                    "end_date": actual_end,     # <-- Заполняем вычисленными датами!
                                    "weekday": weekday,
                                    "slot": pair.get("pair_number") or 1,
                                    "group_uuid": group_uuid,
                                    "subject_uuid": subj_uuid,
                                    "teacher_uuids": teacher_uuids
                                })
                except Exception as e:
                    print(f"Ошибка при загрузке расписания группы {group_num}: {e}")

        # 5. Формируем DTO для создания нового снимка
        now_str = datetime.now(UTC).strftime("%Y-%m-%d %H:%M")
        snapshot_data = ScheduleSnapshotCreate(
            name=f"Синхронизация Raspyx от {now_str}",
            semester_label=sem_label,
            status="active",
            source_type="raspyx",
            is_reference_for_retakes=True,
            groups=groups,
            subjects=list(subjects_map.values()),
            teachers=list(teachers_map.values()),
            schedule_items=schedule_items
        )

        # 6. ПРИНИМАЕМ РЕШЕНИЕ: Обновить или Архивировать?
        current_reference = self.db.scalar(
            select(ScheduleSnapshot).where(ScheduleSnapshot.is_reference_for_retakes.is_(True))
        )

        if current_reference and current_reference.semester_label == sem_label:
            # Это тот же самый семестр! Просто перезаписываем данные (пары, группы и т.д.)
            print(f"[Sync] Обновляем существующий {sem_label} (ID: {current_reference.id})")
            return self.update_snapshot(current_reference.id, snapshot_data)
        else:
            # Это переход на новый семестр. Архивируем старый и создаем новый.
            if current_reference:
                print(f"[Sync] Архивируем прошлый семестр: {current_reference.semester_label}")
                current_reference.is_reference_for_retakes = False
                current_reference.status = "archived"
                # Изменения сохранятся в базе при вызове create_snapshot

            print(f"[Sync] Создаем абсолютно новый {sem_label}")
            return self.create_snapshot(snapshot_data)