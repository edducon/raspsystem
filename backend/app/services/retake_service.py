from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import PastSemester, Retake, RetakeTeacher, TeacherLocal, User
from app.schemas.retake import MergedDayScheduleRequest, RetakeCreateRequest
from app.services.raspyx_service import RaspyxService
from app.services.subject_matching import fuzzy_match, normalize_for_compare


class RetakeService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.raspyx = RaspyxService()

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
        rows = self.db.scalars(
            select(PastSemester)
            .where(PastSemester.group_name == group_name)
            .order_by(PastSemester.subject_name.asc())
        ).all()

        return [
            {
                "subject_name": row.subject_name,
                "teacher_names": list(row.teacher_names or []),
            }
            for row in rows
        ]

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
                detail="Retake was created but could not be reloaded",
            )
        return self._serialize_retake(created, viewer=user)

    def delete_retake(self, retake_id: str, user: User) -> None:
        retake = self.db.scalar(self._retake_query().where(Retake.id == retake_id))
        if retake is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Retake not found",
            )

        if not self._can_delete(retake, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators or the creator can delete this retake",
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

        group_payload = self.raspyx.get_group_schedule(data.group_number)
        group_day = self._schedule_root(group_payload).get(weekday_key)
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
                teacher_payload = self.raspyx.get_teacher_schedule(teacher.full_name)
                teacher_day = self._schedule_root(teacher_payload).get(weekday_key)
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
                detail="Attempt number must be between 1 and 3",
            )
        if data.attempt_number > 1 and not data.chairman_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Chairman is required for second and third attempts",
            )
        if bool(data.room_uuid) == bool(data.link):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either an offline room or an online link",
            )

        duplicates = set(data.main_teacher_uuids) & set(data.commission_teacher_uuids)
        if data.chairman_uuid and (
            data.chairman_uuid in set(data.main_teacher_uuids) or data.chairman_uuid in set(data.commission_teacher_uuids)
        ):
            duplicates.add(data.chairman_uuid)
        if duplicates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher roles must not overlap within the same retake",
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
                detail="One or more selected teachers were not found in the directory",
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
                detail="This retake attempt is already scheduled",
            )

    def _ensure_subject_access(self, user: User, data: RetakeCreateRequest) -> None:
        if user.role == "ADMIN":
            return

        user_departments = set(user.department_ids or [])
        if not user_departments:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No departments are assigned to the current user",
            )

        subject_name = self._resolve_subject_name(data.subject_uuid)
        history_rows = self.db.scalars(select(PastSemester).where(PastSemester.group_name == data.group_number)).all()
        if not history_rows:
            return

        matching_rows = self._match_history_rows(history_rows=history_rows, subject_name=subject_name)
        if not matching_rows:
            return

        history_teacher_names = sorted(
            {
                teacher_name
                for row in matching_rows
                for teacher_name in (row.teacher_names or [])
            }
        )
        if not history_teacher_names:
            return

        history_teachers = self.db.scalars(
            select(TeacherLocal).where(TeacherLocal.full_name.in_(history_teacher_names))
        ).all()
        if not history_teachers:
            return

        has_shared_department = any(
            user_departments.intersection(set(teacher.department_ids or []))
            for teacher in history_teachers
        )
        if not has_shared_department:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This subject belongs to another department",
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
                    detail="Main teachers must belong to one of the user's departments",
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
                    detail="Commission members must share a department with the main teacher",
                )

    def _resolve_subject_name(self, subject_uuid: str) -> str:
        payload = self.raspyx.get_subjects()
        for subject in self._result_items(payload):
            if str(subject.get("uuid")) == subject_uuid:
                return str(subject.get("name") or "")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject was not found in the schedule dictionary",
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
