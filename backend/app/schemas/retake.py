from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RetakeTeacherRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    teacher_uuid: Annotated[str, Field(alias="teacherUuid")]
    full_name: Annotated[str, Field(alias="fullName")]
    role: str


class RetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    group_uuid: Annotated[str, Field(alias="groupUuid")]
    subject_uuid: Annotated[str, Field(alias="subjectUuid")]
    date: str
    time_slots: Annotated[list[int], Field(alias="timeSlots")]
    room_uuid: Annotated[str | None, Field(default=None, alias="roomUuid")]
    link: str | None = None
    attempt_number: Annotated[int, Field(alias="attemptNumber")]
    created_by: Annotated[str | None, Field(default=None, alias="createdBy")]
    created_at: Annotated[datetime | None, Field(default=None, alias="createdAt")]
    can_delete: Annotated[bool, Field(default=False, alias="canDelete")]
    teachers: list[RetakeTeacherRead] = Field(default_factory=list)


class GroupRetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    subject_uuid: Annotated[str, Field(alias="subjectUuid")]
    attempt_number: Annotated[int, Field(alias="attemptNumber")]
    date: str
    created_by: Annotated[str | None, Field(default=None, alias="createdBy")]
    can_delete: Annotated[bool, Field(default=False, alias="canDelete")]


class TeacherRetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    group_uuid: Annotated[str, Field(alias="groupUuid")]
    subject_uuid: Annotated[str, Field(alias="subjectUuid")]
    date: str
    time_slots: Annotated[list[int], Field(alias="timeSlots")]
    room: str | None = None
    link: str | None = None
    attempt_number: Annotated[int, Field(alias="attemptNumber")]
    my_role: Annotated[str, Field(alias="myRole")]


class GroupHistoryEntryRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject_name: Annotated[str, Field(alias="subjectName")]
    teacher_names: Annotated[list[str], Field(default_factory=list, alias="teacherNames")]


class RetakeSubjectOptionRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid: str
    name: str


class RetakeFormContextRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_number: Annotated[str, Field(alias="groupNumber")]
    group_uuid: Annotated[str, Field(alias="groupUuid")]
    subject_uuid: Annotated[str | None, Field(default=None, alias="subjectUuid")]
    main_teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="mainTeacherUuids")]
    commission_teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="commissionTeacherUuids")]
    chairman_uuid: Annotated[str | None, Field(default=None, alias="chairmanUuid")]


class RetakeFormContextRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_history: Annotated[list[GroupHistoryEntryRead], Field(default_factory=list, alias="groupHistory")]
    existing_retakes: Annotated[list[GroupRetakeRead], Field(default_factory=list, alias="existingRetakes")]
    available_subjects: Annotated[list[RetakeSubjectOptionRead], Field(default_factory=list, alias="availableSubjects")]
    subject_blocked_reason: Annotated[str | None, Field(default=None, alias="subjectBlockedReason")]
    assigned_attempts: Annotated[list[int], Field(default_factory=list, alias="assignedAttempts")]
    next_attempt_number: Annotated[int, Field(default=1, alias="nextAttemptNumber")]
    available_main_teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="availableMainTeacherUuids")]
    available_commission_teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="availableCommissionTeacherUuids")]
    available_chairman_uuids: Annotated[list[str], Field(default_factory=list, alias="availableChairmanUuids")]
    main_teacher_lacks_dept: Annotated[bool, Field(default=False, alias="mainTeacherLacksDept")]


class MergedDayDetailsRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject: str
    type: str
    location: str


class MergedDaySlotRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str
    details: MergedDayDetailsRead


class MergedDayScheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_number: Annotated[str, Field(alias="groupNumber")]
    group_uuid: Annotated[str, Field(alias="groupUuid")]
    teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="teacherUuids")]
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        if len(value) != 10:
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")
        return value


class RetakeCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_number: Annotated[str, Field(alias="groupNumber")]
    group_uuid: Annotated[str, Field(alias="groupUuid")]
    subject_uuid: Annotated[str, Field(alias="subjectUuid")]
    date: str
    time_slots: Annotated[list[int], Field(alias="timeSlots")]
    room_uuid: Annotated[str | None, Field(default=None, alias="roomUuid")]
    link: str | None = None
    attempt_number: Annotated[int, Field(default=1, alias="attemptNumber")]
    main_teacher_uuids: Annotated[list[str], Field(alias="mainTeacherUuids")]
    commission_teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="commissionTeacherUuids")]
    chairman_uuid: Annotated[str | None, Field(default=None, alias="chairmanUuid")]

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        if len(value) != 10:
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")
        return value

    @field_validator("time_slots")
    @classmethod
    def validate_time_slots(cls, value: list[int]) -> list[int]:
        unique_slots = sorted(set(value))
        if not unique_slots:
            raise ValueError("Нужно выбрать хотя бы одну пару.")
        if any(slot < 1 or slot > 7 for slot in unique_slots):
            raise ValueError("Номера пар должны быть в диапазоне от 1 до 7.")
        return unique_slots

    @field_validator("main_teacher_uuids")
    @classmethod
    def validate_main_teachers(cls, value: list[str]) -> list[str]:
        unique_teachers = list(dict.fromkeys(value))
        if not unique_teachers:
            raise ValueError("Нужно выбрать хотя бы одного ведущего преподавателя.")
        return unique_teachers