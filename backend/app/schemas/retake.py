from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RetakeTeacherRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    teacher_uuid: str = Field(serialization_alias="teacherUuid")
    full_name: str = Field(serialization_alias="fullName")
    role: str


class RetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    group_uuid: str = Field(serialization_alias="groupUuid")
    subject_uuid: str = Field(serialization_alias="subjectUuid")
    date: str
    time_slots: list[int] = Field(serialization_alias="timeSlots")
    room_uuid: str | None = Field(default=None, serialization_alias="roomUuid")
    link: str | None = None
    attempt_number: int = Field(serialization_alias="attemptNumber")
    created_by: str | None = Field(default=None, serialization_alias="createdBy")
    created_at: datetime | None = Field(default=None, serialization_alias="createdAt")
    can_delete: bool = Field(default=False, serialization_alias="canDelete")
    teachers: list[RetakeTeacherRead] = Field(default_factory=list)


class GroupRetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    subject_uuid: str = Field(serialization_alias="subjectUuid")
    attempt_number: int = Field(serialization_alias="attemptNumber")
    date: str
    created_by: str | None = Field(default=None, serialization_alias="createdBy")
    can_delete: bool = Field(default=False, serialization_alias="canDelete")


class TeacherRetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    group_uuid: str = Field(serialization_alias="groupUuid")
    subject_uuid: str = Field(serialization_alias="subjectUuid")
    date: str
    time_slots: list[int] = Field(serialization_alias="timeSlots")
    room: str | None = None
    link: str | None = None
    attempt_number: int = Field(serialization_alias="attemptNumber")
    my_role: str = Field(serialization_alias="myRole")


class GroupHistoryEntryRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject_name: str = Field(serialization_alias="subjectName")
    teacher_names: list[str] = Field(default_factory=list, serialization_alias="teacherNames")


class RetakeSubjectOptionRead(BaseModel):
    uuid: str
    name: str


class RetakeFormContextRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_number: str = Field(alias="groupNumber")
    group_uuid: str = Field(alias="groupUuid")
    subject_uuid: str | None = Field(default=None, alias="subjectUuid")
    main_teacher_uuids: list[str] = Field(default_factory=list, alias="mainTeacherUuids")
    commission_teacher_uuids: list[str] = Field(default_factory=list, alias="commissionTeacherUuids")
    chairman_uuid: str | None = Field(default=None, alias="chairmanUuid")


class RetakeFormContextRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_history: list[GroupHistoryEntryRead] = Field(default_factory=list, alias="groupHistory")
    existing_retakes: list[GroupRetakeRead] = Field(default_factory=list, alias="existingRetakes")
    available_subjects: list[RetakeSubjectOptionRead] = Field(default_factory=list, alias="availableSubjects")
    subject_blocked_reason: str | None = Field(default=None, alias="subjectBlockedReason")
    assigned_attempts: list[int] = Field(default_factory=list, alias="assignedAttempts")
    next_attempt_number: int = Field(default=1, alias="nextAttemptNumber")
    available_main_teacher_uuids: list[str] = Field(default_factory=list, alias="availableMainTeacherUuids")
    available_commission_teacher_uuids: list[str] = Field(default_factory=list, alias="availableCommissionTeacherUuids")
    available_chairman_uuids: list[str] = Field(default_factory=list, alias="availableChairmanUuids")
    main_teacher_lacks_dept: bool = Field(default=False, alias="mainTeacherLacksDept")


class MergedDayDetailsRead(BaseModel):
    subject: str
    type: str
    location: str


class MergedDaySlotRead(BaseModel):
    reason: str
    details: MergedDayDetailsRead


class MergedDayScheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_number: str = Field(serialization_alias="groupNumber")
    group_uuid: str = Field(serialization_alias="groupUuid")
    teacher_uuids: list[str] = Field(default_factory=list, serialization_alias="teacherUuids")
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        if len(value) != 10:
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")
        return value


class RetakeCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_number: str = Field(serialization_alias="groupNumber")
    group_uuid: str = Field(serialization_alias="groupUuid")
    subject_uuid: str = Field(serialization_alias="subjectUuid")
    date: str
    time_slots: list[int] = Field(serialization_alias="timeSlots")
    room_uuid: str | None = Field(default=None, serialization_alias="roomUuid")
    link: str | None = None
    attempt_number: int = Field(default=1, serialization_alias="attemptNumber")
    main_teacher_uuids: list[str] = Field(serialization_alias="mainTeachersUuids")
    commission_teacher_uuids: list[str] = Field(default_factory=list, serialization_alias="commissionTeachersUuids")
    chairman_uuid: str | None = Field(default=None, serialization_alias="chairmanUuid")

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
