from __future__ import annotations

import re
from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException, status
from sqlalchemy import Select, delete, select
from sqlalchemy.orm import Session, selectinload

from app.models import PastSemester, Retake, RetakeAttemptRule, RetakeLeadTeacher, RetakeMeeting, RetakeTeacher, TeacherLocal, User
from app.schemas.retake import MergedDayScheduleRequest, RetakeCreateRequest, RetakeFormContextRequest, RetakeUpdateRequest
from app.services.raspyx_service import RaspyxService
from app.services.reference_schedule_service import ReferenceScheduleService
from app.services.subject_matching import clean_subject_name, fuzzy_match, normalize_for_compare


GROUP_NAME_NORMALIZER_RE = re.compile(r"[\s\u00A0]+")
TEACHER_NAME_NORMALIZER_RE = re.compile(r"[\s\u00A0]+")


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
            self._retake_query()
            .where(Retake.group_uuid == group_uuid)
            .order_by(Retake.attempt_number.asc(), Retake.date.asc(), Retake.created_at.asc())
        ).all()
        return [self._serialize_retake(retake, viewer=viewer) for retake in retakes]

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
        main_teacher_options: list[dict] = []
        auto_created_main_teacher_names: list[str] = []
        unresolved_main_teacher_names: list[str] = []
        main_teacher_department_required_names: list[str] = []
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
                main_teacher_context = self._available_main_teacher_context(
                    user=user,
                    history_rows=history_rows,
                    subject_uuid=payload.subject_uuid,
                )
                available_main_teacher_uuids = main_teacher_context["available_main_teacher_uuids"]
                main_teacher_options = main_teacher_context["main_teacher_options"]
                auto_created_main_teacher_names = main_teacher_context["auto_created_main_teacher_names"]
                unresolved_main_teacher_names = main_teacher_context["unresolved_main_teacher_names"]
                main_teacher_department_required_names = main_teacher_context["main_teacher_department_required_names"]

        main_teacher_lacks_dept = False
        available_commission_teacher_uuids: list[str] = []
        available_chairman_uuids: list[str] = []
        available_meetings: list[dict] = []
        department_id: int | None = None
        if include_teacher_data and payload.main_teacher_uuids:
            commission_context = self._build_commission_context(
                main_teacher_uuids=payload.main_teacher_uuids,
                commission_teacher_uuids=payload.commission_teacher_uuids,
                chairman_uuid=payload.chairman_uuid,
            )
            main_teacher_lacks_dept = commission_context["main_teacher_lacks_dept"]
            available_commission_teacher_uuids = commission_context["available_commission_teacher_uuids"]
            available_chairman_uuids = commission_context["available_chairman_uuids"]
            department_id = commission_context["department_id"]

        return {
            "group_history": group_history,
            "existing_retakes": existing_retakes,
            "available_subjects": available_subjects,
            "subject_blocked_reason": subject_blocked_reason,
            "assigned_attempts": assigned_attempts,
            "next_attempt_number": next_attempt_number,
            "available_main_teacher_uuids": available_main_teacher_uuids,
            "main_teacher_options": main_teacher_options,
            "auto_created_main_teacher_names": auto_created_main_teacher_names,
            "unresolved_main_teacher_names": unresolved_main_teacher_names,
            "main_teacher_department_required_names": main_teacher_department_required_names,
            "available_commission_teacher_uuids": available_commission_teacher_uuids,
            "available_chairman_uuids": available_chairman_uuids,
            "available_meetings": available_meetings,
            "attempt_rules": self.list_attempt_rules(),
            "department_id": department_id,
            "main_teacher_lacks_dept": main_teacher_lacks_dept,
        }

    def list_my_retakes(self, user: User) -> list[dict]:
        if not user.teacher_uuid:
            return []
        rows = self.db.execute(
            select(Retake, RetakeTeacher.role)
            .join(RetakeTeacher, Retake.id == RetakeTeacher.retake_id)
            .where(RetakeTeacher.teacher_uuid == user.teacher_uuid)
            .where(RetakeTeacher.role != "MAIN")
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
                "link": self._effective_link(retake),
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
        department_id = self._resolve_retake_department_id(data=data, user=user, teacher_map=teacher_map)
        self._ensure_subject_access(user=user, data=data)
        self._ensure_teacher_access(user=user, data=data, teacher_map=teacher_map, department_id=department_id)
        self._ensure_attempt_is_available(data)
        meeting = self._resolve_or_create_meeting(data=data, user=user, department_id=department_id)

        retake = Retake(
            group_uuid=data.group_uuid,
            subject_uuid=data.subject_uuid,
            date=data.date,
            time_slots=list(data.time_slots),
            room_uuid=data.room_uuid,
            link=data.link if meeting is None else None,
            meeting_id=meeting.id if meeting is not None else None,
            department_id=department_id,
            attempt_number=data.attempt_number,
            created_by=str(user.id),
        )
        self.db.add(retake)
        self.db.flush()

        for teacher_uuid in data.main_teacher_uuids:
            self.db.add(RetakeLeadTeacher(retake_id=retake.id, teacher_uuid=teacher_uuid))
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

    def update_retake(self, retake_id: str, data: RetakeUpdateRequest, user: User) -> dict:
        retake = self.db.scalar(self._retake_query().where(Retake.id == retake_id))
        if retake is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пересдача не найдена.")
        if not self._can_manage_department(retake.department_id, user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к пересдаче другой кафедры.")

        self._validate_create_payload(data)
        teacher_map = self._load_teacher_map(
            data.main_teacher_uuids + data.commission_teacher_uuids + ([data.chairman_uuid] if data.chairman_uuid else [])
        )
        department_id = self._resolve_retake_department_id(data=data, user=user, teacher_map=teacher_map)
        self._ensure_subject_access(user=user, data=data)
        self._ensure_teacher_access(user=user, data=data, teacher_map=teacher_map, department_id=department_id)
        self._ensure_attempt_is_available(data, exclude_retake_id=retake_id)
        meeting = self._resolve_or_create_meeting(data=data, user=user, department_id=department_id)

        retake.group_uuid = data.group_uuid
        retake.subject_uuid = data.subject_uuid
        retake.date = data.date
        retake.time_slots = list(data.time_slots)
        retake.room_uuid = data.room_uuid if not data.is_online else None
        retake.link = data.link if meeting is None else None
        retake.meeting_id = meeting.id if meeting is not None else None
        retake.department_id = department_id
        retake.attempt_number = data.attempt_number

        self.db.execute(delete(RetakeLeadTeacher).where(RetakeLeadTeacher.retake_id == retake_id))
        self.db.execute(delete(RetakeTeacher).where(RetakeTeacher.retake_id == retake_id))

        for teacher_uuid in data.main_teacher_uuids:
            self.db.add(RetakeLeadTeacher(retake_id=retake.id, teacher_uuid=teacher_uuid))
        for teacher_uuid in data.commission_teacher_uuids:
            self.db.add(RetakeTeacher(retake_id=retake.id, teacher_uuid=teacher_uuid, role="COMMISSION"))
        if data.chairman_uuid:
            self.db.add(RetakeTeacher(retake_id=retake.id, teacher_uuid=data.chairman_uuid, role="CHAIRMAN"))

        self.db.commit()

        updated = self.db.scalar(self._retake_query().where(Retake.id == retake.id))
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Пересдача обновлена, но не удалось загрузить её данные.",
            )
        return self._serialize_retake(updated, viewer=user)

    def delete_retake(self, retake_id: str, user: User) -> None:
        retake = self.db.scalar(self._retake_query().where(Retake.id == retake_id))
        if retake is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пересдача не найдена.")
        if not self._can_delete(retake, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Удалить пересдачу может только администратор или сотрудник той же кафедры.",
            )
        self.db.delete(retake)
        self.db.commit()

    def list_meeting_candidates(self, date: str, user: User, department_id: int | None = None) -> list[dict]:
        if len(date) != 10:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Дата должна быть в формате ГГГГ-ММ-ДД.")
        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            if department_id is not None and department_id not in user_departments:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к встречам другой кафедры.")
            if department_id is None and user_departments:
                meetings: list[dict] = []
                for user_department_id in sorted(user_departments):
                    meetings.extend(self._list_meeting_candidates(date=date, department_id=user_department_id, teacher_uuids=[]))
                seen: set[str] = set()
                result: list[dict] = []
                for meeting in meetings:
                    if meeting["id"] in seen:
                        continue
                    seen.add(meeting["id"])
                    result.append(meeting)
                return result
            if department_id is None:
                return []
        return self._list_meeting_candidates(date=date, department_id=department_id, teacher_uuids=[])

    def update_meeting(self, meeting_id: str, link: str | None, title: str | None, user: User) -> dict:
        meeting = self.db.scalar(
            select(RetakeMeeting)
            .options(selectinload(RetakeMeeting.retakes))
            .where(RetakeMeeting.id == meeting_id)
        )
        if meeting is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Встреча не найдена.")
        if not self._can_manage_department(meeting.department_id, user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к встрече другой кафедры.")
        meeting.link = link.strip() if link else None
        meeting.title = title.strip() if title else None
        self.db.commit()
        self.db.refresh(meeting)
        return self._serialize_meeting(meeting)

    def list_attempt_rules(self) -> list[dict]:
        self._ensure_attempt_rules()
        rules = self.db.scalars(select(RetakeAttemptRule).order_by(RetakeAttemptRule.attempt_number.asc())).all()
        return [self._serialize_attempt_rule(rule) for rule in rules]

    def update_attempt_rule(
        self,
        attempt_number: int,
        requires_chairman: bool,
        min_commission_members: int,
    ) -> dict:
        if attempt_number not in {1, 2, 3}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Номер попытки должен быть от 1 до 3.")
        if min_commission_members < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Минимум членов комиссии не может быть отрицательным.")

        self._ensure_attempt_rules()
        rule = self.db.get(RetakeAttemptRule, attempt_number)
        if rule is None:
            rule = RetakeAttemptRule(attempt_number=attempt_number)
            self.db.add(rule)

        rule.requires_chairman = requires_chairman
        rule.min_commission_members = min_commission_members
        self.db.commit()
        self.db.refresh(rule)
        return self._serialize_attempt_rule(rule)

    def get_merged_day_schedule(self, data: MergedDayScheduleRequest) -> dict[str, dict | None]:
        schedule = {str(slot): None for slot in range(1, 8)}
        date_value = datetime.strptime(data.date, "%Y-%m-%d")
        weekday_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        weekday_key = weekday_names[date_value.weekday()]
        if weekday_key == "sunday":
            return schedule

        db_retakes = self.db.scalars(select(Retake).where(Retake.date == data.date)).all()
        checked_retakes = [
            retake
            for retake in db_retakes
            if not data.exclude_retake_id or retake.id != data.exclude_retake_id
        ]

        for retake in checked_retakes:
            if retake.group_uuid != data.group_uuid:
                continue
            for slot in retake.time_slots:
                schedule[str(slot)] = {
                    "reason": "Занято (пересдача)",
                    "details": {
                        "subject": "Пересдача уже назначена в системе",
                        "type": f"Попытка {retake.attempt_number}",
                        "location": "Онлайн" if self._effective_link(retake) else (retake.room_uuid or "Очно"),
                    },
                }

        if data.teacher_uuids and checked_retakes:
            busy_rows = self.db.execute(
                select(RetakeTeacher.retake_id, RetakeTeacher.teacher_uuid, TeacherLocal.full_name)
                .join(TeacherLocal, RetakeTeacher.teacher_uuid == TeacherLocal.uuid)
                .where(RetakeTeacher.retake_id.in_([retake.id for retake in checked_retakes]))
                .where(RetakeTeacher.role != "MAIN")
            ).all()

            retake_by_id = {retake.id: retake for retake in checked_retakes}
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
            .options(selectinload(Retake.lead_teacher_links).selectinload(RetakeLeadTeacher.teacher))
            .options(selectinload(Retake.meeting).selectinload(RetakeMeeting.retakes))
            .order_by(Retake.date.asc(), Retake.attempt_number.asc(), Retake.created_at.asc())
        )

    def _serialize_retake(self, retake: Retake, viewer: User | None = None) -> dict:
        teachers = []
        seen_lead_uuids: set[str] = set()
        for lead_link in sorted(retake.lead_teacher_links, key=lambda item: item.teacher_uuid):
            if lead_link.teacher is None:
                continue
            seen_lead_uuids.add(lead_link.teacher_uuid)
            teachers.append(
                {
                    "teacher_uuid": lead_link.teacher_uuid,
                    "full_name": lead_link.teacher.full_name,
                    "role": "MAIN",
                }
            )
        for teacher_link in sorted(
            retake.teacher_links,
            key=lambda item: (self._teacher_role_weight(item.role), item.teacher_uuid),
        ):
            if teacher_link.teacher is None:
                continue
            if teacher_link.role == "MAIN" and teacher_link.teacher_uuid in seen_lead_uuids:
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
            "link": self._effective_link(retake),
            "meeting_id": retake.meeting_id,
            "department_id": retake.department_id,
            "attempt_number": retake.attempt_number,
            "created_by": retake.created_by,
            "created_at": retake.created_at,
            "can_delete": self._can_delete(retake, viewer),
            "teachers": teachers,
            "meeting": self._serialize_meeting(retake.meeting) if retake.meeting else None,
        }

    def _effective_link(self, retake: Retake) -> str | None:
        if retake.meeting is not None:
            return retake.meeting.link
        return retake.link

    def _serialize_meeting(self, meeting: RetakeMeeting) -> dict:
        retakes = sorted(
            meeting.retakes or [],
            key=lambda item: (min(item.time_slots or [99]), item.group_uuid, item.attempt_number),
        )
        return {
            "id": meeting.id,
            "department_id": meeting.department_id,
            "date": meeting.date,
            "link": meeting.link,
            "title": meeting.title,
            "retake_count": len(retakes),
            "retakes": [
                {
                    "id": retake.id,
                    "group_uuid": retake.group_uuid,
                    "subject_uuid": retake.subject_uuid,
                    "subject_name": self._resolve_subject_name_safe(retake.subject_uuid),
                    "attempt_number": retake.attempt_number,
                    "time_slots": list(retake.time_slots or []),
                }
                for retake in retakes
            ],
        }

    def _list_meeting_candidates(
        self,
        date: str | None,
        department_id: int | None,
        teacher_uuids: list[str],
    ) -> list[dict]:
        if not date:
            return []

        query = select(RetakeMeeting).options(selectinload(RetakeMeeting.retakes))
        query = query.where(RetakeMeeting.date == date)
        if department_id is not None:
            query = query.where(RetakeMeeting.department_id == department_id)

        meetings = list(self.db.scalars(query.order_by(RetakeMeeting.created_at.desc())).all())
        if not teacher_uuids:
            return [self._serialize_meeting(meeting) for meeting in meetings[:20]]

        requested = set(teacher_uuids)
        ranked: list[tuple[int, RetakeMeeting]] = []
        for meeting in meetings:
            participant_uuids = {
                link.teacher_uuid
                for retake in meeting.retakes
                for link in (retake.teacher_links or [])
                if link.role != "MAIN"
            }
            score = len(requested.intersection(participant_uuids))
            ranked.append((score, meeting))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [self._serialize_meeting(meeting) for _, meeting in ranked[:20]]

    def _can_delete(self, retake: Retake, viewer: User | None) -> bool:
        if viewer is None:
            return False
        return self._can_manage_department(retake.department_id, viewer)

    def _can_manage_department(self, department_id: int | None, viewer: User | None) -> bool:
        if viewer is None:
            return False
        if viewer.role == "ADMIN":
            return True
        if viewer.role != "EMPLOYEE" or department_id is None:
            return False
        return department_id in set(viewer.department_ids or [])

    def _serialize_attempt_rule(self, rule: RetakeAttemptRule) -> dict:
        return {
            "attempt_number": rule.attempt_number,
            "requires_chairman": rule.requires_chairman,
            "min_commission_members": rule.min_commission_members,
        }

    def _default_attempt_rules(self) -> list[RetakeAttemptRule]:
        return [
            RetakeAttemptRule(attempt_number=1, requires_chairman=False, min_commission_members=1),
            RetakeAttemptRule(attempt_number=2, requires_chairman=True, min_commission_members=0),
            RetakeAttemptRule(attempt_number=3, requires_chairman=True, min_commission_members=0),
        ]

    def _ensure_attempt_rules(self) -> None:
        existing_numbers = set(self.db.scalars(select(RetakeAttemptRule.attempt_number)).all())
        missing_rules = [rule for rule in self._default_attempt_rules() if rule.attempt_number not in existing_numbers]
        if not missing_rules:
            return
        self.db.add_all(missing_rules)
        self.db.commit()

    def _attempt_rule_for(self, attempt_number: int) -> RetakeAttemptRule:
        self._ensure_attempt_rules()
        rule = self.db.get(RetakeAttemptRule, attempt_number)
        if rule is not None:
            return rule
        default_rules = {rule.attempt_number: rule for rule in self._default_attempt_rules()}
        return default_rules.get(attempt_number, RetakeAttemptRule(attempt_number=attempt_number))

    def _teacher_role_weight(self, role: str) -> int:
        return {"MAIN": 1, "CHAIRMAN": 2, "COMMISSION": 3}.get(role, 99)

    def _validate_create_payload(self, data: RetakeCreateRequest) -> None:
        if data.attempt_number not in {1, 2, 3}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Номер попытки должен быть от 1 до 3.")
        rule = self._attempt_rule_for(data.attempt_number)
        if rule.requires_chairman and not data.chairman_uuid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Для выбранной попытки нужно выбрать председателя комиссии.")
        if len(data.commission_teacher_uuids) < rule.min_commission_members:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Для выбранной попытки нужно выбрать членов комиссии: минимум {rule.min_commission_members}.",
            )
        if not data.room_uuid and not data.is_online and not data.link and not data.meeting_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Укажите очную аудиторию или онлайн-формат.")
        if data.room_uuid and (data.link or data.meeting_id or data.is_online):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Для очной пересдачи нельзя одновременно указывать онлайн-ссылку.")
        if data.link and data.meeting_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Укажите новую ссылку или выберите существующую встречу, но не оба варианта сразу.")

        duplicates = set()
        if data.chairman_uuid and data.chairman_uuid in data.commission_teacher_uuids:
            duplicates.add(data.chairman_uuid)
        if duplicates:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Один преподаватель не может быть одновременно председателем и членом комиссии.")

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

    def _resolve_retake_department_id(
        self,
        data: RetakeCreateRequest,
        user: User,
        teacher_map: dict[str, TeacherLocal],
    ) -> int | None:
        if data.department_id is not None:
            if user.role != "ADMIN":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Вручную выбрать кафедру может только администратор.")
            return data.department_id

        main_teachers = [teacher_map[uuid] for uuid in data.main_teacher_uuids if uuid in teacher_map]
        if not main_teachers:
            return None

        common_departments = set(main_teachers[0].department_ids or [])
        for teacher in main_teachers[1:]:
            common_departments.intersection_update(set(teacher.department_ids or []))
        if not common_departments:
            return None

        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            allowed = sorted(common_departments.intersection(user_departments))
            if allowed:
                return allowed[0]

        return sorted(common_departments)[0]

    def _resolve_or_create_meeting(
        self,
        data: RetakeCreateRequest,
        user: User,
        department_id: int | None,
    ) -> RetakeMeeting | None:
        if data.room_uuid and not data.is_online:
            return None

        if data.meeting_id:
            meeting = self.db.scalar(select(RetakeMeeting).where(RetakeMeeting.id == data.meeting_id))
            if meeting is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Выбранная встреча не найдена.")
            if meeting.date != data.date:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Встреча должна быть на ту же дату.")
            if department_id and meeting.department_id and meeting.department_id != department_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Встреча относится к другой кафедре.")
            return meeting

        if data.is_online or data.link:
            meeting = RetakeMeeting(
                department_id=department_id,
                date=data.date,
                link=data.link or None,
                title=None,
                created_by=str(user.id),
            )
            self.db.add(meeting)
            self.db.flush()
            return meeting

        return None

    def _ensure_attempt_is_available(self, data: RetakeCreateRequest, exclude_retake_id: str | None = None) -> None:
        selected_subject_name = self._resolve_subject_name(data.subject_uuid)
        candidates = self.db.scalars(
            select(Retake).where(
                Retake.group_uuid == data.group_uuid,
                Retake.attempt_number == data.attempt_number,
            )
        ).all()
        for retake in candidates:
            if exclude_retake_id is not None and retake.id == exclude_retake_id:
                continue
            if normalize_for_compare(self._resolve_subject_name_safe(retake.subject_uuid)) == normalize_for_compare(selected_subject_name):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Эта попытка уже назначена.")

    def _ensure_subject_access(self, user: User, data: RetakeCreateRequest) -> None:
        error_message = self._get_subject_access_error(user=user, group_number=data.group_number, subject_uuid=data.subject_uuid)
        if error_message is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)

    def _ensure_teacher_access(
        self,
        user: User,
        data: RetakeCreateRequest,
        teacher_map: dict[str, TeacherLocal],
        department_id: int | None,
    ) -> None:
        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            if not department_id or department_id not in user_departments:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Кафедра пересдачи не относится к вашим кафедрам.",
                )

        if department_id:
            participant_uuids = list(data.commission_teacher_uuids)
            if data.chairman_uuid:
                participant_uuids.append(data.chairman_uuid)

            invalid_commission = [
                uuid
                for uuid in participant_uuids
                if department_id not in set(teacher_map[uuid].department_ids or [])
            ]
            if invalid_commission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Комиссия должна быть с кафедры пересдачи.",
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

    def _available_main_teacher_context(
        self,
        user: User,
        history_rows: list[PastSemester],
        subject_uuid: str,
    ) -> dict[str, object]:
        subject_name = self._resolve_subject_name(subject_uuid)
        matching_rows = self._match_history_rows(history_rows=history_rows, subject_name=subject_name)
        history_teacher_names = self._unique_teacher_names([
            teacher_name
            for row in matching_rows
            for teacher_name in (row.teacher_names or [])
        ])

        if not history_teacher_names:
            return {
                "available_main_teacher_uuids": [],
                "main_teacher_options": [],
                "auto_created_main_teacher_names": [],
                "unresolved_main_teacher_names": [],
                "main_teacher_department_required_names": [],
            }

        teacher_result = self._load_or_create_teachers_by_names(history_teacher_names, user=user)
        teachers: list[TeacherLocal] = teacher_result["teachers"]

        if user.role != "ADMIN":
            user_departments = set(user.department_ids or [])
            teachers = [teacher for teacher in teachers if user_departments.intersection(set(teacher.department_ids or []))]
        return {
            "available_main_teacher_uuids": [teacher.uuid for teacher in teachers],
            "main_teacher_options": [self._serialize_teacher_option(teacher) for teacher in teachers],
            "auto_created_main_teacher_names": teacher_result["auto_created_names"],
            "unresolved_main_teacher_names": teacher_result["unresolved_names"],
            "main_teacher_department_required_names": teacher_result["department_required_names"],
        }

    def _serialize_teacher_option(self, teacher: TeacherLocal) -> dict:
        return {
            "uuid": teacher.uuid,
            "full_name": teacher.full_name,
            "department_ids": list(teacher.department_ids or []),
        }

    def _unique_teacher_names(self, teacher_names: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for teacher_name in teacher_names:
            normalized_name = self._normalize_teacher_name(teacher_name)
            comparable_name = self._normalize_teacher_for_compare(normalized_name)
            if not normalized_name or comparable_name in seen:
                continue
            seen.add(comparable_name)
            result.append(normalized_name)
        return sorted(result, key=lambda value: value.casefold())

    def _normalize_teacher_name(self, teacher_name: str) -> str:
        return TEACHER_NAME_NORMALIZER_RE.sub(" ", str(teacher_name or "")).strip()

    def _normalize_teacher_for_compare(self, teacher_name: str) -> str:
        return self._normalize_teacher_name(teacher_name).replace("ё", "е").casefold()

    def _auto_teacher_department_id(self, user: User) -> int | None:
        user_departments = sorted(set(user.department_ids or []))
        return user_departments[0] if len(user_departments) == 1 else None

    def _load_or_create_teachers_by_names(self, teacher_names: list[str], user: User) -> dict[str, object]:
        normalized_names = [self._normalize_teacher_name(name) for name in teacher_names]
        normalized_names = [name for name in normalized_names if name]
        if not normalized_names:
            return {
                "teachers": [],
                "auto_created_names": [],
                "unresolved_names": [],
                "department_required_names": [],
            }

        pool = list(self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name.asc())).all())
        teachers_by_name = {
            self._normalize_teacher_for_compare(teacher.full_name): teacher
            for teacher in pool
        }
        department_id = self._auto_teacher_department_id(user)

        teachers: list[TeacherLocal] = []
        auto_created_names: list[str] = []
        unresolved_names: list[str] = []
        department_required_names: list[str] = []
        created_or_updated = False

        for teacher_name in normalized_names:
            comparable_name = self._normalize_teacher_for_compare(teacher_name)
            teacher = teachers_by_name.get(comparable_name)
            if teacher is None:
                if department_id is None:
                    department_required_names.append(teacher_name)
                    unresolved_names.append(teacher_name)
                    continue
                teacher_uuid = str(uuid5(NAMESPACE_URL, f"teacher-local:{comparable_name}"))
                teacher = self.db.get(TeacherLocal, teacher_uuid)
                if teacher is None:
                    teacher = TeacherLocal(
                        uuid=teacher_uuid,
                        full_name=teacher_name,
                        department_ids=[department_id],
                    )
                    self.db.add(teacher)
                    auto_created_names.append(teacher_name)
                    created_or_updated = True
                teachers_by_name[comparable_name] = teacher

            if not teacher.department_ids and department_id is not None:
                teacher.department_ids = [department_id]
                created_or_updated = True
                if teacher_name not in auto_created_names:
                    auto_created_names.append(teacher_name)

            teachers.append(teacher)

        if created_or_updated:
            self.db.commit()

        return {
            "teachers": teachers,
            "auto_created_names": sorted(set(auto_created_names), key=lambda value: value.casefold()),
            "unresolved_names": sorted(set(unresolved_names), key=lambda value: value.casefold()),
            "department_required_names": sorted(set(department_required_names), key=lambda value: value.casefold()),
        }

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
        normalized_names = {self._normalize_teacher_for_compare(name) for name in teacher_names if name}
        if not normalized_names:
            return []

        pool = list(self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name.asc())).all())
        result: list[TeacherLocal] = []
        seen_uuids: set[str] = set()
        for teacher in pool:
            if self._normalize_teacher_for_compare(teacher.full_name) not in normalized_names:
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
                "department_id": None,
            }

        main_departments = set(teachers_list[0].department_ids or [])
        for teacher in teachers_list[1:]:
            main_departments.intersection_update(set(teacher.department_ids or []))

        main_teacher_lacks_dept = bool(main_teacher_uuids) and not main_departments
        department_id = min(main_departments) if main_departments else None
        if not main_departments:
            return {
                "main_teacher_lacks_dept": main_teacher_lacks_dept,
                "available_commission_teacher_uuids": [],
                "available_chairman_uuids": [],
                "department_id": None,
            }

        pool = list(self.db.scalars(select(TeacherLocal).order_by(TeacherLocal.full_name.asc())).all())
        allowed_pool = [teacher for teacher in pool if main_departments.intersection(set(teacher.department_ids or []))]

        selected_commission_uuids = set(commission_teacher_uuids)

        return {
            "main_teacher_lacks_dept": main_teacher_lacks_dept,
            "available_commission_teacher_uuids": [
                teacher.uuid
                for teacher in allowed_pool
                if teacher.uuid != chairman_uuid
            ],
            "available_chairman_uuids": [
                teacher.uuid
                for teacher in allowed_pool
                if teacher.uuid not in selected_commission_uuids
            ],
            "department_id": department_id,
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
            raw_subject_name = str(row.subject_name or "").strip()
            subject_name = clean_subject_name(raw_subject_name)
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
