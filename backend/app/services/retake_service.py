from __future__ import annotations

import re
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import PastSemester, Retake, RetakeTeacher, TeacherLocal, User
from app.schemas.retake import MergedDayScheduleRequest, RetakeCreateRequest, RetakeFormContextRequest
from app.services.raspyx_service import RaspyxService
from app.services.reference_schedule_service import ReferenceScheduleService
from app.services.subject_matching import clean_subject_name, fuzzy_match, normalize_for_compare


GROUP_NAME_NORMALIZER_RE = re.compile(r"[\s\u00A0]+")


class RetakeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.raspyx = RaspyxService()
        self.reference_schedule = ReferenceScheduleService(db)

    def list_retakes(self, viewer: User | None = None) -> list[dict]:
        retakes = self.db.scalars(self._retake_query()).all()
        return [self._serialize_retake(retake, viewer=viewer) for retake in retakes]

    def list_group_retakes(self, group_uuid: str, viewer: User) -> list[dict]:
        retakes = self.db.scalars(
            select(Retake)
            .where(Retake.group_uuid == group_uuid)
            .order_by(Retake.attempt_number.asc(), Retake.date.asc(), Retake.created_at.asc())
        ).all()
        return [
            {
                "id": retake.id,
                "subject_uuid": retake.subject_uuid,
                "subject_name": self._resolve_subject_name_safe(retake.subject_uuid),
                "attempt_number": retake.attempt_number,
                "date": retake.date,
                "created_by": retake.created_by,
                "can_delete": self._can_delete(retake, viewer),
            }
            for retake in retakes
        ]

    def list_group_history(self, group_name: str) -> list[dict]:
        rows = self._load_group_history_rows(group_name)
        return self._serialize_history_rows(rows)

    def get_form_context(self, payload: RetakeFormContextRequest, user: User) -> dict:
        include_group_data = payload.include_group_data
        include_subject_data = payload.include_subject_data
        include_teacher_data = payload.include_teacher_data

        history_rows: list[PastSemester] = []
        if include_group_data or include_subject_data:
            history_rows = self._load_group_history_rows(payload.group_number)

        group_history: list[dict] = []
        available_subjects: list[dict] = []
        if include_group_data:
            group_history = self._serialize_history_rows(history_rows)
            available_subjects = self._build_available_subjects(
                history_rows=history_rows,
                group_uuid=payload.group_uuid,
                group_number=payload.group_number,
            )

        existing_retakes: list[dict] = []
        if include_group_data or (include_subject_data and payload.subject_uuid):
            existing_retakes = self.list_group_retakes(group_uuid=payload.group_uuid, viewer=user)

        subject_blocked_reason = None
        assigned_attempts: list[int] = []
        next_attempt_number = 1
        available_main_teacher_uuids: list[str] = []
        if include_subject_data and payload.subject_uuid:
            subject_blocked_reason = self._get_subject_access_error(
                user=user,
                group_number=payload.group_number,
                subject_uuid=payload.subject_uuid,
            )
            selected_subject_name = self._resolve_subject_name(payload.subject_uuid)
            assigned_attempts = sorted(
                {
                    int(retake["attempt_number"])
                    for retake in existing_retakes
                    if normalize_for_compare(str(retake.get("subject_name") or "")) == normalize_for_compare(selected_subject_name)
                }
            )
            next_attempt_number = next((value for value in (1, 2, 3) if value not in assigned_attempts), 3)

            if subject_blocked_reason is None:
                available_main_teacher_uuids = self._available_main_teacher_uuids(
                    user=user,
                    history_rows=history_rows,
                    group_number=payload.group_number,
                    group_uuid=payload.group_uuid,
                    subject_uuid=payload.subject_uuid,
                )

        main_teacher_lacks_dept = False
        available_commission_teacher_uuids: list[str] = []
        available_chairman_uuids: list[str] = []
        if include_teacher_data and payload.main_teacher_uuids:
            commission_context = self._build_commission_context(
                main_teacher_uuids=payload.main_teacher_uuids,
                commission_teacher_uuids=payload.commission_teacher_uuids,
                chairman_uuid=payload.chairman_uuid,
            )
            main_teacher_lacks_dept = commission_context["main_teacher_lacks_dept"]
            available_commission_teacher_uuids = commission_context["available_commission_teacher_uuids"]
            available_chairman_uuids = commission_context["available_chairman_uuids"]

        return {
            "group_history": group_history,
            "existing_retakes": existing_retakes,
            "available_subjects": available_subjects,
            "subject_blocked_reason": subject_blocked_reason,
            "assigned_attempts": assigned_attempts,
            "next_attempt_number": next_attempt_number,
            "available_main_teacher_uuids": available_main_teacher_uuids,
            "available_commission_teacher_uuids": available_commission_teacher_uuids,
            "available_chairman_uuids": available_chairman_uuids,
            "main_teacher_lacks_dept": main_teacher_lacks_dept,
        }

    def list_my_retakes(self, user: User) -> list[dict]:
        if not user.teacher_uuid:
            return []
        rows = self.db.execute(
            select(Retake, RetakeTeacher.role)
            .join(RetakeTeacher, Retake.id == RetakeTeacher.retake_id)
            .where(RetakeTeacher.teacher_uuid == user.teacher_uuid)
            .order_by(Retake.date.asc(), Retake.attempt_number.asc(), Retake.created_at.asc())
        ).all()
        return [
            {
                "id": retake.id,
                "group_uuid": retake.group_uuid,
                "subject_uuid": retake.subject_uuid,
                "subject_name": self._resolve_subject_name_safe(retake.subject_uuid),
                "date": retake.date,
                "time_slots": list(retake.time_slots or []),
                "room": retake.room_uuid,
                "link": retake.link,
                "attempt_number": retake.attempt_number,
                "my_role": role,
            }
            for retake, role in rows
        ]

    def create_retake(self, data: RetakeCreateRequest, user: User) -> dict:
        self._validate_create_payload(data)
        teacher_map = self._load_teacher_map(
            data.main_teacher_uuids + data.commission_teacher_uuids + ([data.chairman_uuid] if data.chairman_uuid else [])
        )
        self._ensure_subject_access(user=user, data=data)
        self._ensure_teacher_access(user=user, data=data, teacher_map=teacher_map)
        self._ensure_attempt_is_available(data)

        retake = Retake(
            group_uuid=data.group_uuid,
            subject_uuid=data.subject_uuid,
            date=data.date,
            time_slots=list(data.time_slots),
            room_uuid=data.room_uuid,
            link=data.link,
            attempt_number=data.attempt_number,
            created_by=str(user.id),
        )
        self.db.add(retake)
        self.db.flush()

        for teacher_uuid in data.main_teacher_uuids:
            self.db.add(RetakeTeacher(retake_id=retake.id, teacher_uuid=teacher_uuid, role="MAIN"))
        for teacher_uuid in data.commission_teacher_uuids:
            self.db.add(RetakeTeacher(retake_id=retake.id, teacher_uuid=teacher_uuid, role="COMMISSION"))
        if data.chairman_uuid:
            self.db.add(RetakeTeacher(retake_id=retake.id, teacher_uuid=data.chairman_uuid, role="CHAIRMAN"))

        self.db.commit()

        created = self.db.scalar(self._retake_query().where(Retake.id == retake.id))
        if created is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Пересдача создана, но не удалось загрузить её данные.",
            )
        return self._serialize_retake(created, viewer=user)

    def delete_retake(self, retake_id: str, user: User) -> None:
        retake = self.db.scalar(self._retake_query().where(Retake.id == retake_id))
        if retake is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пересдача не найдена.")
        if not self._can_delete(retake, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Удалить пересдачу может только администратор или её автор.",
            )
        self.db.delete(retake)
        self.db.commit()

    def get_merged_day_schedule(self, data: MergedDayScheduleRequest) -> dict[str, dict | None]:
        schedule = {str(slot): None for slot in range(1, 8)}
        date_value = datetime.strptime(data.date, "%Y-%m-%d")
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekday_key = weekday_names[date_value.weekday()]
        if weekday_key == "sunday":
            return schedule

        db_retakes = self.db.scalars(select(Retake).where(Retake.date == data.date)).all()

        for retake in db_retakes:
            if retake.group_uuid != data.group_uuid:
                continue
            for slot in retake.time_slots:
                schedule[str(slot)] = {
                    "reason": "Занято (пересдача)",
                    "details": {
                        "subject": "Пересдача уже назначена в системе",
                        "type": f"Попытка {retake.attempt_number}",
                        "location": "Онлайн" if retake.link else (retake.room_uuid or "Очно"),
                    },
                }

        if data.teacher_uuids and db_retakes:
            busy_rows = self.db.execute(
                select(RetakeTeacher.retake_id, RetakeTeacher.teacher_uuid, TeacherLocal.full_name)
                .join(TeacherLocal, RetakeTeacher.teacher_uuid == TeacherLocal.uuid)
                .where(RetakeTeacher.retake_id.in_([retake.id for retake in db_retakes]))
            ).all()

            retake_by_id = {retake.id: retake for retake in db_retakes}
            requested_teacher_uuids = set(data.teacher_uuids)
            for retake_id, teacher_uuid, full_name in busy_rows:
                if teacher_uuid not in requested_teacher_uuids:
                    continue
                retake = retake_by_id.get(retake_id)
                if retake is None:
                    continue
                short_name = full_name.split(" ")[0]
                for slot in retake.time_slots:
                    current = schedule[str(slot)]
                    if current is not None and short_name in current["reason"]:
                        continue
                    schedule[str(slot)] = {
                        "reason": f"Занято (пересдача у {short_name})",
                        "details": {
                            "subject": "Преподаватель уже участвует в пересдаче",
                            "type": "Комиссия",
                            "location": "В системе",
                        },
                    }

        group_root = self._group_schedule_root(data.group_number)
        group_day = self._schedule_day_root(group_root, target_date=date_value, weekday_key=weekday_key)
        if isinstance(group_day, dict):
            for slot in range(1, 8):
                active_pair = self._find_active_pair(group_day.get(str(slot)), date_value)
                if active_pair is None:
                    continue
                previous = schedule[str(slot)]
                schedule[str(slot)] = {
                    "reason": f"{previous['reason']} + пара" if previous else "Занято у группы по расписанию",
                    "details": {
                        "subject": self._pair_subject_name(active_pair, default="Предмет не указан"),
                        "type": self._pair_subject_type(active_pair, default="Тип не указан"),
                        "location": self._format_pair_location(active_pair),
                    },
                }

        if data.teacher_uuids:
            teachers = self.db.scalars(select(TeacherLocal).where(TeacherLocal.uuid.in_(data.teacher_uuids))).all()
            for teacher in teachers:
                teacher_root = self._teacher_schedule_root(teacher.full_name)
                teacher_day = self._schedule_day_root(teacher_root, target_date=date_value, weekday_key=weekday_key)
                if not isinstance(teacher_day, dict):
                    continue
                short_name = teacher.full_name.split(" ")[0]
                for slot in range(1, 8):
                    active_pair = self._find_active_pair(teacher_day.get(str(slot)), date_value)
                    if active_pair is None:
                        continue
                    current = schedule[str(slot)]
                    if current is None:
                        schedule[str(slot)] = {
                            "reason": f"Пара у {short_name}",
                            "details": {
                                "subject": self._pair_subject_name(active_pair, default="Предмет"),
                                "type": self._pair_subject_type(active_pair, default="Тип"),
                                "location": self._format_pair_location(active_pair),
                            },
                        }
                    elif short_name not in current["reason"]:
                        current["reason"] += f" + {short_name}"

        return schedule

    def _retake_query(self) -> Select[tuple[Retake]]:
        return (
            select(Retake)
            .options(selectinload(Retake.teacher_links).selectinload(RetakeTeacher.teacher))
            .order_by(Retake.date.asc(), Retake.attempt_number.asc(), Retake.created_at.asc())
        )

    def _serialize_retake(self, retake: Retake, viewer: User | None = None) -> dict:
        teachers = []
        for teacher_link in sorted(
            retake.teacher_links,
            key=lambda item: (self._teacher_role_weight(item.role), item.teacher_uuid),
        ):
            if teacher_link.teacher is None:
                continue
            teachers.append(
                {
                    "teacher_uuid": teacher_link.teacher_uuid,
                    "full_name": teacher_link.teacher.full_name,
                    "role": teacher_link.role,
                }
            )
        return {
            "id": retake.id,
            "group_uuid": retake.group_uuid,
            "subject_uuid": retake.subject_uuid,
            "subject_name": self._resolve_subject_name_safe(retake.subject_uuid),
            "date": retake.date,
            "time_slots": list(retake.time_slots or []),
            "room_uuid": retake.room_uuid,
            "link": retake.link,
            "attempt_number": retake.attempt_number,
            "created_by": retake.created_by,
            "created_at": retake.created_at,
            "can_delete": self._can_delete(retake, viewer),
            "teachers": teachers,
        }

    def _can_delete(self, retake: Retake, viewer: User | None) -> bool:
        if viewer is None:
            return False
        return viewer.role == "ADMIN" or retake.created_by == str(viewer.id)

    def _teacher_role_weight(self, role: str) -> int:
        return {"MAIN": 1, "CHAIRMAN": 2, "COMMISSION": 3}.get(role, 99)

    def _validate_create_payload(self, data: RetakeCreateRequest) -> None:
        if data.attempt_number not in {1, 2, 3}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Номер попытки должен быть от 1 до 3.")
        if data.attempt_number > 1 and not data.chairman_uuid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Для 2-й и 3-й попытки нужен председатель комиссии.")
        if bool(data.room_uuid) == bool(data.link):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Укажите аудиторию или ссылку, но не оба поля сразу.")

        duplicates = set(data.main_teacher_uuids) & set(data.commission_teacher_uuids)
        if data.chairman_uuid and (data.chairman_uuid in data.main_teacher_uuids or data.chairman_uuid in data.commission_teacher_uuids):
            duplicates.add(data.chairman_uuid)
        if duplicates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Один преподаватель не может иметь несколько ролей.")

    def _load_teacher_map(self, teacher_uuids: list[str]) -> dict[str, TeacherLocal]:
        unique_uuids = list(dict.fromkeys([uuid for uuid in teacher_uuids if uuid]))
        if not unique_uuids:
            return {}
        teachers = self.db.scalars(select(TeacherLocal).where(TeacherLocal.uuid.in_(unique_uuids))).all()
        teacher_map = {teacher.uuid: teacher for teacher in teachers}
        missing = [uuid for uuid in unique_uuids if uuid not in teacher_map]
        if missing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некоторые преподаватели отсутствуют в справочнике.")
        return teacher_map

    def _ensure_attempt_is_available(self, data: RetakeCreateRequest) -> None:
        selected_subject_name = self._resolve_subject_name(data.subject_uuid)
        candidates = self.db.scalars(
            select(Retake).where(
                Retake.group_uuid == data.group_uuid,
                Retake.attempt_number == data.attempt_number,
            )
        ).all()
        for retake in candidates:
            if normalize_for_compare(self._resolve_subject_name_safe(retake.subject_uuid)) == normalize_for_compare(selected_subject_name):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Эта попытка уже назначена.")

    def _ensure_subject_access(self, user: User, data: RetakeCreateRequest) -> None:
        error_message = self._get_subject_access_error(user=user, group_number=data.group_number, subject_uuid=data.subject_uuid)
        if error_message is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)

    def _ensure_teacher_access(self, user: User, data: RetakeCreateRequest, teacher_map: dict[str, TeacherLocal]) -> None:
        main_teachers = [teacher_map[uuid] for uuid in data.main_teacher_uuids]
        if not main_teachers:
            return

        main_departments = set(main_teachers[0].department_ids or [])
        for teacher in main_teachers[1:]:
            main_departments.intersection_update(set(teacher.department_ids or []))

        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            if not main_departments or not user_departments.intersection(main_departments):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ведущие преподаватели не относятся к вашей кафедре.",
                )

        if main_departments:
            commission_uuids = list(data.commission_teacher_uuids)
            if data.chairman_uuid:
                commission_uuids.append(data.chairman_uuid)

            invalid_commission = [
                uuid
                for uuid in commission_uuids
                if not main_departments.intersection(set(teacher_map[uuid].department_ids or []))
            ]
            if invalid_commission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Комиссия должна быть с той же кафедры, что и ведущие преподаватели.",
                )

    def _resolve_subject_name(self, subject_uuid: str) -> str:
        reference_name = self.reference_schedule.find_subject_name(subject_uuid)
        if reference_name:
            return reference_name

        history_name = self._find_history_subject_name(subject_uuid)
        if history_name:
            return history_name

        for subject in self._list_schedule_subjects():
            if str(subject.get("uuid") or "") == subject_uuid:
                return str(subject.get("name") or "")

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Дисциплина не найдена в текущем семестре.")

    def _match_history_rows(self, history_rows: list[PastSemester], subject_name: str) -> list[PastSemester]:
        normalized_target = normalize_for_compare(subject_name)
        exact_matches = [row for row in history_rows if normalize_for_compare(row.subject_name) == normalized_target]
        if exact_matches:
            return exact_matches
        return [row for row in history_rows if fuzzy_match(row.subject_name, subject_name)]

    def _result_items(self, payload: object) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        result = payload.get("result") or payload.get("response") or []
        return result if isinstance(result, list) else []

    def _schedule_root(self, payload: object) -> dict:
        if not isinstance(payload, dict):
            return {}
        root = payload.get("result") or payload.get("response") or {}
        return root if isinstance(root, dict) else {}

    def _find_active_pair(self, pairs: object, target_date: datetime) -> dict | None:
        if not isinstance(pairs, list):
            return None
        target_value = target_date.timestamp()
        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            start_date = pair.get("start_date")
            end_date = pair.get("end_date")
            if not start_date or not end_date:
                return pair
            try:
                start_value = datetime.fromisoformat(str(start_date)).timestamp()
                end_value = datetime.fromisoformat(str(end_date)).timestamp()
            except ValueError:
                return pair
            if start_value <= target_value <= end_value:
                return pair
        return None

    def _format_pair_location(self, pair: dict) -> str:
        location_name = self._safe_nested(pair, "location", "name", default="")
        rooms = pair.get("rooms")
        room_number = ""
        if isinstance(rooms, list) and rooms and isinstance(rooms[0], dict):
            room_number = str(rooms[0].get("number") or "")
        if location_name and room_number:
            return f"{location_name} ({room_number})"
        if location_name:
            return location_name
        if room_number:
            return room_number
        return "Аудитория не указана"

    def _safe_nested(self, source: dict, *keys: str, default: str) -> str:
        current: object = source
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
        return str(current) if current else default

    def _pair_subject_name(self, pair: dict, default: str) -> str:
        subject = pair.get("subject")
        if isinstance(subject, dict):
            for key in ("name", "title", "subject_name", "subjectName"):
                value = str(subject.get(key) or "").strip()
                if value:
                    return value
        if isinstance(subject, str) and subject.strip():
            return subject.strip()
        return default

    def _pair_subject_type(self, pair: dict, default: str) -> str:
        subject_type = pair.get("subject_type")
        if isinstance(subject_type, dict):
            for key in ("type", "name", "title"):
                value = str(subject_type.get(key) or "").strip()
                if value:
                    return value
        if isinstance(subject_type, str) and subject_type.strip():
            return subject_type.strip()
        pair_type = str(pair.get("type") or "").strip()
        return pair_type or default

    def _normalize_group_name(self, value: str) -> str:
        return GROUP_NAME_NORMALIZER_RE.sub("", value).casefold()

    def _load_group_history_rows(self, group_name: str) -> list[PastSemester]:
        exact_rows = list(
            self.db.scalars(
                select(PastSemester).where(PastSemester.group_name == group_name).order_by(PastSemester.subject_name.asc())
            ).all()
        )
        if exact_rows:
            return exact_rows

        normalized_target = self._normalize_group_name(group_name)
        if not normalized_target:
            return []

        candidates = list(self.db.scalars(select(PastSemester).order_by(PastSemester.subject_name.asc())).all())
        return [row for row in candidates if self._normalize_group_name(row.group_name) == normalized_target]

    def _serialize_history_rows(self, rows: list[PastSemester]) -> list[dict]:
        return [{"subject_name": row.subject_name, "teacher_names": list(row.teacher_names or [])} for row in rows]

    def _build_available_subjects(self, history_rows: list[PastSemester], group_uuid: str, group_number: str) -> list[dict]:
        group_subjects = self._list_group_current_subjects(group_uuid=group_uuid, group_number=group_number)
        if group_subjects:
            history_names = [row.subject_name for row in history_rows]
            matched = self._match_subject_options_by_names(group_subjects, history_names)
            return matched or self._dedupe_subject_options(group_subjects)

        current_subjects = self._list_schedule_subjects()
        if current_subjects:
            history_names = [row.subject_name for row in history_rows]
            matched = self._match_subject_options_by_names(current_subjects, history_names)
            if matched:
                return matched

        return []

    def _list_schedule_subjects(self) -> list[dict]:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.list_subjects()
        return self._result_items(self.raspyx.get_subjects())

    def _list_group_current_subjects(self, group_uuid: str, group_number: str) -> list[dict]:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.get_group_subjects(group_uuid)

        current_subjects = self._list_schedule_subjects()
        root = self._group_schedule_root(group_number)
        subject_names = sorted(self._collect_subject_names_from_schedule(root))
        if not subject_names:
            return []
        return self._match_subject_options_by_names(current_subjects, subject_names)

    def _match_subject_options_by_names(self, current_subjects: list[dict], names: list[str]) -> list[dict]:
        if not current_subjects or not names:
            return []

        normalized_names = {normalize_for_compare(name) for name in names if name}
        ranked_matches: list[tuple[int, int, str, str, str]] = []
        for subject in current_subjects:
            subject_uuid = str(subject.get("uuid") or "")
            subject_name = str(subject.get("name") or "").strip()
            if not subject_uuid or not subject_name:
                continue

            normalized_subject_name = normalize_for_compare(subject_name)
            if normalized_subject_name in normalized_names:
                score = 0
            elif any(fuzzy_match(name, subject_name) for name in names if name):
                score = 1
            else:
                continue

            ranked_matches.append(
                (
                    score,
                    len(clean_subject_name(subject_name)),
                    subject_name.casefold(),
                    subject_uuid,
                    subject_name,
                )
            )

        ranked_matches.sort()

        result: list[dict] = []
        seen_uuids: set[str] = set()
        seen_names: set[str] = set()
        for _, _, _, subject_uuid, subject_name in ranked_matches:
            normalized_subject_name = normalize_for_compare(subject_name)
            if subject_uuid in seen_uuids or normalized_subject_name in seen_names:
                continue
            seen_uuids.add(subject_uuid)
            seen_names.add(normalized_subject_name)
            result.append({"uuid": subject_uuid, "name": subject_name})

        return sorted(result, key=lambda item: item["name"])

    def _dedupe_subject_options(self, subjects: list[dict]) -> list[dict]:
        result: list[dict] = []
        seen_names: set[str] = set()
        for subject in sorted(subjects, key=lambda item: str(item.get("name") or "").casefold()):
            subject_uuid = str(subject.get("uuid") or "")
            subject_name = str(subject.get("name") or "").strip()
            if not subject_uuid or not subject_name:
                continue
            normalized_subject_name = normalize_for_compare(subject_name)
            if normalized_subject_name in seen_names:
                continue
            seen_names.add(normalized_subject_name)
            result.append({"uuid": subject_uuid, "name": subject_name})
        return result

    def _collect_subject_names_from_schedule(self, value: object) -> set[str]:
        result: set[str] = set()
        for pair in self._iter_schedule_pairs(value):
            subject_name = self._pair_subject_name(pair, default="").strip()
            if subject_name:
                result.add(subject_name)
        return result

    def _available_main_teacher_uuids(
        self,
        user: User,
        history_rows: list[PastSemester],
        group_number: str,
        group_uuid: str,
        subject_uuid: str,
    ) -> list[str]:
        subject_name = self._resolve_subject_name(subject_uuid)
        matching_rows = self._match_history_rows(history_rows=history_rows, subject_name=subject_name)
        history_teacher_names = sorted({teacher_name for row in matching_rows for teacher_name in (row.teacher_names or [])})

        teacher_name_sources: list[list[str]] = []
        if history_teacher_names:
            teacher_name_sources.append(history_teacher_names)

        if self.reference_schedule.has_reference_snapshot():
            snapshot_teacher_names = self.reference_schedule.get_group_subject_teacher_names(group_uuid, subject_uuid)
            if snapshot_teacher_names:
                teacher_name_sources.append(snapshot_teacher_names)

        teachers: list[TeacherLocal] = []
        for teacher_names in teacher_name_sources:
            teachers = self._load_teachers_by_names(teacher_names)
            if teachers:
                break
        if not teachers:
            return []

        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            teachers = [teacher for teacher in teachers if user_departments.intersection(set(teacher.department_ids or []))]
        return [teacher.uuid for teacher in teachers]

    def _get_live_group_subject_teacher_names(self, group_number: str, subject_name: str) -> list[str]:
        if self.reference_schedule.has_reference_snapshot():
            return []

        teacher_names: set[str] = set()
        root = self._group_schedule_root(group_number)
        for pair in self._iter_schedule_pairs(root):
            if not fuzzy_match(self._pair_subject_name(pair, default=""), subject_name):
                continue
            for teacher in pair.get("teachers") or []:
                full_name = self._extract_teacher_name(teacher)
                if full_name:
                    teacher_names.add(full_name)
        return sorted(teacher_names)

    def _load_teachers_by_names(self, teacher_names: list[str]) -> list[TeacherLocal]:
        normalized_names = {normalize_for_compare(name) for name in teacher_names if name}
        if not normalized_names:
            return []

        pool = list(self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name.asc())).all())
        result: list[TeacherLocal] = []
        seen_uuids: set[str] = set()
        for teacher in pool:
            if normalize_for_compare(teacher.full_name) not in normalized_names:
                continue
            if teacher.uuid in seen_uuids:
                continue
            seen_uuids.add(teacher.uuid)
            result.append(teacher)
        return result

    def _iter_schedule_pairs(self, value: object) -> list[dict]:
        if not isinstance(value, dict):
            return []

        result: list[dict] = []
        for day_payload in value.values():
            if not isinstance(day_payload, dict):
                continue
            for slot_payload in day_payload.values():
                if not isinstance(slot_payload, list):
                    continue
                for pair in slot_payload:
                    if isinstance(pair, dict):
                        result.append(pair)
        return result

    def _extract_teacher_name(self, value: object) -> str:
        if isinstance(value, str):
            return value.strip()
        if not isinstance(value, dict):
            return ""

        for key in ("full_name", "fullName", "fio", "teacher_fio", "name"):
            candidate = str(value.get(key) or "").strip()
            if candidate:
                return candidate
        return ""

    def _build_commission_context(self, main_teacher_uuids: list[str], commission_teacher_uuids: list[str], chairman_uuid: str | None) -> dict[str, object]:
        selected_main = self._load_teacher_map(main_teacher_uuids)
        teachers_list = list(selected_main.values())

        if not teachers_list:
            return {
                "main_teacher_lacks_dept": False,
                "available_commission_teacher_uuids": [],
                "available_chairman_uuids": [],
            }

        main_departments = set(teachers_list[0].department_ids or [])
        for teacher in teachers_list[1:]:
            main_departments.intersection_update(set(teacher.department_ids or []))

        main_teacher_lacks_dept = bool(main_teacher_uuids) and not main_departments
        if not main_departments:
            return {
                "main_teacher_lacks_dept": main_teacher_lacks_dept,
                "available_commission_teacher_uuids": [],
                "available_chairman_uuids": [],
            }

        pool = list(self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name.asc())).all())
        allowed_pool = [teacher for teacher in pool if main_departments.intersection(set(teacher.department_ids or []))]

        selected_main_uuids = set(main_teacher_uuids)
        selected_commission_uuids = set(commission_teacher_uuids)

        return {
            "main_teacher_lacks_dept": main_teacher_lacks_dept,
            "available_commission_teacher_uuids": [
                teacher.uuid
                for teacher in allowed_pool
                if teacher.uuid not in selected_main_uuids and teacher.uuid != chairman_uuid
            ],
            "available_chairman_uuids": [
                teacher.uuid
                for teacher in allowed_pool
                if teacher.uuid not in selected_main_uuids and teacher.uuid not in selected_commission_uuids
            ],
        }

    def _get_subject_access_error(self, user: User, group_number: str, subject_uuid: str | None) -> str | None:
        if user.role == "ADMIN" or not subject_uuid:
            return None
        user_departments = set(user.department_ids or [])
        if not user_departments:
            return "У вас не указаны кафедры."

        subject_name = self._resolve_subject_name(subject_uuid)
        history_rows = self._load_group_history_rows(group_number)
        if not history_rows:
            return None

        matching_rows = self._match_history_rows(history_rows=history_rows, subject_name=subject_name)
        if not matching_rows:
            return None

        history_teacher_names = sorted({teacher_name for row in matching_rows for teacher_name in (row.teacher_names or [])})
        if not history_teacher_names:
            return None

        history_teachers = self.db.scalars(select(TeacherLocal).where(TeacherLocal.full_name.in_(history_teacher_names))).all()
        if not history_teachers:
            return None

        common_depts = set(history_teachers[0].department_ids or [])
        for teacher in history_teachers[1:]:
            common_depts.intersection_update(set(teacher.department_ids or []))

        has_shared_department = bool(user_departments.intersection(common_depts))
        return None if has_shared_department else "Эта дисциплина относится к другой кафедре."

    def _build_available_subjects(self, history_rows: list[PastSemester], group_uuid: str, group_number: str) -> list[dict]:
        if not history_rows:
            return []

        history_subjects = self._dedupe_history_subjects(history_rows)

        return [
            {
                "uuid": self._history_subject_uuid(subject_name),
                "name": subject_name,
            }
            for subject_name, normalized_name in history_subjects
        ]

    def _dedupe_history_subjects(self, history_rows: list[PastSemester]) -> list[tuple[str, str]]:
        result: list[tuple[str, str]] = []
        seen_names: set[str] = set()
        ordered_rows = sorted(history_rows, key=lambda row: clean_subject_name(row.subject_name).casefold())

        for row in ordered_rows:
            subject_name = str(row.subject_name or "").strip()
            normalized_subject_name = normalize_for_compare(subject_name)
            if not subject_name or not normalized_subject_name or normalized_subject_name in seen_names:
                continue
            seen_names.add(normalized_subject_name)
            result.append((subject_name, normalized_subject_name))

        return result

    def _history_subject_uuid(self, subject_name: str) -> str:
        normalized_subject_name = normalize_for_compare(subject_name)
        return str(uuid5(NAMESPACE_URL, f"retake-history-subject:{normalized_subject_name}"))

    def _find_history_subject_name(self, subject_uuid: str) -> str | None:
        history_rows = list(self.db.scalars(select(PastSemester).order_by(PastSemester.subject_name.asc())).all())
        for subject_name, _ in self._dedupe_history_subjects(history_rows):
            if self._history_subject_uuid(subject_name) == subject_uuid:
                return subject_name
        return None

    def _resolve_subject_name(self, subject_uuid: str) -> str:
        reference_name = self.reference_schedule.find_subject_name(subject_uuid)
        if reference_name:
            return reference_name

        history_name = self._find_history_subject_name(subject_uuid)
        if history_name:
            return history_name

        for subject in self._list_schedule_subjects():
            if str(subject.get("uuid") or "") == subject_uuid:
                return str(subject.get("name") or "")

        history_name = self._find_history_subject_name(subject_uuid)
        if history_name:
            return history_name

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Дисциплина не найдена.")

    def _resolve_subject_name_safe(self, subject_uuid: str) -> str:
        try:
            return self._resolve_subject_name(subject_uuid)
        except HTTPException:
            return "Неизвестная дисциплина"

    def _schedule_day_root(self, root: dict, target_date: datetime, weekday_key: str) -> dict | None:
        weekday_day = root.get(weekday_key)
        if isinstance(weekday_day, dict):
            return weekday_day

        date_key = target_date.strftime("%Y-%m-%d")
        exact_day = root.get(date_key)
        return exact_day if isinstance(exact_day, dict) else None

    def _group_schedule_root(self, group_number: str) -> dict:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.build_group_schedule_root(group_number)
        return self._schedule_root(self.raspyx.get_group_schedule(group_number))

    def _teacher_schedule_root(self, teacher_full_name: str) -> dict:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.build_teacher_schedule_root(teacher_full_name)
        return self._schedule_root(self.raspyx.get_teacher_schedule(teacher_full_name))
