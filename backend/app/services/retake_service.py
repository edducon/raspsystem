from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import PastSemester, Retake, RetakeTeacher, TeacherLocal, User
from app.schemas.retake import MergedDayScheduleRequest, RetakeCreateRequest, RetakeFormContextRequest
from app.services.reference_schedule_service import ReferenceScheduleService
from app.services.raspyx_service import RaspyxService
from app.services.subject_matching import fuzzy_match, normalize_for_compare


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
        history_rows = self._load_group_history_rows(payload.group_number)
        group_history = self._serialize_history_rows(history_rows)
        existing_retakes = self.list_group_retakes(group_uuid=payload.group_uuid, viewer=user)
        available_subjects = self._build_available_subjects(history_rows, payload.group_uuid)
        subject_blocked_reason = self._get_subject_access_error(
            user=user,
            group_number=payload.group_number,
            subject_uuid=payload.subject_uuid,
        )
        assigned_attempts = sorted(
            {
                int(retake["attempt_number"])
                for retake in existing_retakes
                if payload.subject_uuid and retake["subject_uuid"] == payload.subject_uuid
            }
        )
        next_attempt_number = next((value for value in (1, 2, 3) if value not in assigned_attempts), 3)

        available_main_teacher_uuids: list[str] = []
        if payload.subject_uuid and subject_blocked_reason is None:
            available_main_teacher_uuids = self._available_main_teacher_uuids(
                user=user,
                history_rows=history_rows,
                group_uuid=payload.group_uuid,
                subject_uuid=payload.subject_uuid,
            )

        main_teacher_lacks_dept = False
        available_commission_teacher_uuids: list[str] = []
        available_chairman_uuids: list[str] = []
        if payload.main_teacher_uuids:
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
                detail="Пересдача создана, но не удалось заново загрузить её данные.",
            )
        return self._serialize_retake(created, viewer=user)

    def delete_retake(self, retake_id: str, user: User) -> None:
        retake = self.db.scalar(self._retake_query().where(Retake.id == retake_id))
        if retake is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Пересдача не найдена.",
            )

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
                    "reason": "Занято (Пересдача)",
                    "details": {
                        "subject": "Назначена пересдача в системе",
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
                        "reason": f"Занято (Пересдача у: {short_name})",
                        "details": {
                            "subject": "Принимает пересдачу",
                            "type": "Комиссия",
                            "location": "В системе",
                        },
                    }

        group_day = self._group_schedule_root(data.group_number).get(weekday_key)
        if isinstance(group_day, dict):
            for slot in range(1, 8):
                active_pair = self._find_active_pair(group_day.get(str(slot)), date_value)
                if active_pair is None:
                    continue

                previous = schedule[str(slot)]
                schedule[str(slot)] = {
                    "reason": f"{previous['reason']} + Пара" if previous else "Занято у группы (По расписанию)",
                    "details": {
                        "subject": self._safe_nested(active_pair, "subject", "name", default="Предмет не указан"),
                        "type": self._safe_nested(active_pair, "subject_type", "type", default="Тип не указан"),
                        "location": self._format_pair_location(active_pair),
                    },
                }

        if data.teacher_uuids:
            teachers = self.db.scalars(
                select(TeacherLocal).where(TeacherLocal.uuid.in_(data.teacher_uuids))
            ).all()
            for teacher in teachers:
                teacher_day = self._teacher_schedule_root(teacher.full_name).get(weekday_key)
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
                            "reason": f"Пара у: {short_name}",
                            "details": {
                                "subject": self._safe_nested(active_pair, "subject", "name", default="Предмет"),
                                "type": self._safe_nested(active_pair, "subject_type", "type", default="Тип"),
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
        for teacher_link in sorted(retake.teacher_links, key=lambda item: (self._teacher_role_weight(item.role), item.teacher_uuid)):
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Номер попытки должен быть от 1 до 3.",
            )
        if data.attempt_number > 1 and not data.chairman_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для второй и третьей попытки нужно указать председателя комиссии.",
            )
        if bool(data.room_uuid) == bool(data.link):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Укажите либо аудиторию, либо ссылку для онлайн-формата.",
            )

        duplicates = set(data.main_teacher_uuids) & set(data.commission_teacher_uuids)
        if data.chairman_uuid and (
            data.chairman_uuid in set(data.main_teacher_uuids) or data.chairman_uuid in set(data.commission_teacher_uuids)
        ):
            duplicates.add(data.chairman_uuid)
        if duplicates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Один и тот же преподаватель не может иметь несколько ролей в одной пересдаче.",
            )

    def _load_teacher_map(self, teacher_uuids: list[str]) -> dict[str, TeacherLocal]:
        unique_uuids = list(dict.fromkeys([uuid for uuid in teacher_uuids if uuid]))
        if not unique_uuids:
            return {}

        teachers = self.db.scalars(select(TeacherLocal).where(TeacherLocal.uuid.in_(unique_uuids))).all()
        teacher_map = {teacher.uuid: teacher for teacher in teachers}
        missing = [uuid for uuid in unique_uuids if uuid not in teacher_map]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Один или несколько выбранных преподавателей отсутствуют в справочнике.",
            )
        return teacher_map

    def _ensure_attempt_is_available(self, data: RetakeCreateRequest) -> None:
        existing = self.db.scalar(
            select(Retake).where(
                Retake.group_uuid == data.group_uuid,
                Retake.subject_uuid == data.subject_uuid,
                Retake.attempt_number == data.attempt_number,
            )
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Эта попытка пересдачи уже назначена.",
            )

    def _ensure_subject_access(self, user: User, data: RetakeCreateRequest) -> None:
        error_message = self._get_subject_access_error(
            user=user,
            group_number=data.group_number,
            subject_uuid=data.subject_uuid,
        )
        if error_message is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_message,
            )

    def _ensure_teacher_access(self, user: User, data: RetakeCreateRequest, teacher_map: dict[str, TeacherLocal]) -> None:
        main_teachers = [teacher_map[uuid] for uuid in data.main_teacher_uuids]
        main_departments = {
            department_id
            for teacher in main_teachers
            for department_id in (teacher.department_ids or [])
        }

        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            if any(
                teacher.department_ids and not user_departments.intersection(set(teacher.department_ids))
                for teacher in main_teachers
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ведущие преподаватели должны относиться к одной из кафедр пользователя.",
                )

        if main_departments:
            commission_uuids = list(data.commission_teacher_uuids)
            if data.chairman_uuid:
                commission_uuids.append(data.chairman_uuid)

            invalid_commission = [
                uuid
                for uuid in commission_uuids
                if teacher_map[uuid].department_ids and not main_departments.intersection(set(teacher_map[uuid].department_ids))
            ]
            if invalid_commission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Члены комиссии должны быть с той же кафедры, что и ведущий преподаватель.",
                )

    def _resolve_subject_name(self, subject_uuid: str) -> str:
        reference_name = self.reference_schedule.find_subject_name(subject_uuid)
        if reference_name:
            return reference_name

        payload = self.raspyx.get_subjects()
        for subject in self._result_items(payload):
            if str(subject.get("uuid")) == subject_uuid:
                return str(subject.get("name") or "")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дисциплина не найдена в справочнике расписания.",
        )

    def _match_history_rows(self, history_rows: list[PastSemester], subject_name: str) -> list[PastSemester]:
        normalized_target = normalize_for_compare(subject_name)
        exact_matches = [
            row
            for row in history_rows
            if normalize_for_compare(row.subject_name) == normalized_target
        ]
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

    def _safe_nested(self, source: dict, *keys: str, default: str) -> str:
        current: object = source
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
        return str(current) if current else default

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

    def _load_group_history_rows(self, group_name: str) -> list[PastSemester]:
        return list(
            self.db.scalars(
                select(PastSemester)
                .where(PastSemester.group_name == group_name)
                .order_by(PastSemester.subject_name.asc())
            ).all()
        )

    def _serialize_history_rows(self, rows: list[PastSemester]) -> list[dict]:
        return [
            {
                "subject_name": row.subject_name,
                "teacher_names": list(row.teacher_names or []),
            }
            for row in rows
        ]

    def _build_available_subjects(self, history_rows: list[PastSemester], group_uuid: str) -> list[dict]:
        if not history_rows:
            return self.reference_schedule.get_group_subjects(group_uuid) if self.reference_schedule.has_reference_snapshot() else []

        history_names = [row.subject_name for row in history_rows]
        normalized_history_names = {normalize_for_compare(name) for name in history_names}
        schedule_subjects = self._list_schedule_subjects()

        exact_matches = [
            subject
            for subject in schedule_subjects
            if normalize_for_compare(str(subject.get("name") or "")) in normalized_history_names
        ]
        fuzzy_matches = [
            subject
            for subject in schedule_subjects
            if any(fuzzy_match(history_name, str(subject.get("name") or "")) for history_name in history_names)
        ]

        result: list[dict] = []
        seen_uuids: set[str] = set()
        for subject in [*exact_matches, *fuzzy_matches]:
            subject_uuid = str(subject.get("uuid") or "")
            subject_name = str(subject.get("name") or "")
            if not subject_uuid or not subject_name or subject_uuid in seen_uuids:
                continue
            seen_uuids.add(subject_uuid)
            result.append({"uuid": subject_uuid, "name": subject_name})

        if result:
            return sorted(result, key=lambda item: item["name"])

        return self.reference_schedule.get_group_subjects(group_uuid) if self.reference_schedule.has_reference_snapshot() else []

    def _list_schedule_subjects(self) -> list[dict]:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.list_subjects()
        return [
            {
                "uuid": str(item.get("uuid") or ""),
                "name": str(item.get("name") or ""),
            }
            for item in self._result_items(self.raspyx.get_subjects())
            if item.get("uuid") and item.get("name")
        ]

    def _available_main_teacher_uuids(
        self,
        user: User,
        history_rows: list[PastSemester],
        group_uuid: str,
        subject_uuid: str,
    ) -> list[str]:
        subject_name = self._resolve_subject_name(subject_uuid)
        matching_rows = self._match_history_rows(history_rows=history_rows, subject_name=subject_name)
        history_teacher_names = sorted(
            {
                teacher_name
                for row in matching_rows
                for teacher_name in (row.teacher_names or [])
            }
        )
        if not history_teacher_names and self.reference_schedule.has_reference_snapshot():
            history_teacher_names = self.reference_schedule.get_group_subject_teacher_names(group_uuid, subject_uuid)
        if not history_teacher_names:
            return []

        teachers = list(
            self.db.scalars(
                select(TeacherLocal)
                .where(TeacherLocal.full_name.in_(history_teacher_names))
                .order_by(TeacherLocal.full_name.asc())
            ).all()
        )
        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            teachers = [
                teacher
                for teacher in teachers
                if user_departments.intersection(set(teacher.department_ids or []))
            ]

        return [teacher.uuid for teacher in teachers]

    def _build_commission_context(
        self,
        main_teacher_uuids: list[str],
        commission_teacher_uuids: list[str],
        chairman_uuid: str | None,
    ) -> dict[str, object]:
        selected_main = self._load_teacher_map(main_teacher_uuids)
        main_departments = {
            department_id
            for teacher in selected_main.values()
            for department_id in (teacher.department_ids or [])
        }

        main_teacher_lacks_dept = bool(main_teacher_uuids) and not main_departments
        if not main_departments:
            return {
                "main_teacher_lacks_dept": main_teacher_lacks_dept,
                "available_commission_teacher_uuids": [],
                "available_chairman_uuids": [],
            }

        pool = list(
            self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name.asc())).all()
        )
        allowed_pool = [
            teacher
            for teacher in pool
            if main_departments.intersection(set(teacher.department_ids or []))
        ]
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

    def _get_subject_access_error(
        self,
        user: User,
        group_number: str,
        subject_uuid: str | None,
    ) -> str | None:
        if user.role == "ADMIN" or not subject_uuid:
            return None

        user_departments = set(user.department_ids or [])
        if not user_departments:
            return "У текущего пользователя не указаны кафедры."

        subject_name = self._resolve_subject_name(subject_uuid)
        history_rows = self._load_group_history_rows(group_number)
        if not history_rows:
            return None

        matching_rows = self._match_history_rows(history_rows=history_rows, subject_name=subject_name)
        if not matching_rows:
            return None

        history_teacher_names = sorted(
            {
                teacher_name
                for row in matching_rows
                for teacher_name in (row.teacher_names or [])
            }
        )
        if not history_teacher_names:
            return None

        history_teachers = self.db.scalars(
            select(TeacherLocal).where(TeacherLocal.full_name.in_(history_teacher_names))
        ).all()
        if not history_teachers:
            return None

        has_shared_department = any(
            user_departments.intersection(set(teacher.department_ids or []))
            for teacher in history_teachers
        )
        return None if has_shared_department else "Эта дисциплина относится к другой кафедре."

    def _group_schedule_root(self, group_number: str) -> dict:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.build_group_schedule_root(group_number)
        return self._schedule_root(self.raspyx.get_group_schedule(group_number))

    def _teacher_schedule_root(self, teacher_full_name: str) -> dict:
        if self.reference_schedule.has_reference_snapshot():
            return self.reference_schedule.build_teacher_schedule_root(teacher_full_name)
        return self._schedule_root(self.raspyx.get_teacher_schedule(teacher_full_name))
