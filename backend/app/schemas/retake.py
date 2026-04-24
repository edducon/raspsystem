from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class RetakeTeacherRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    teacher_uuid: str
    full_name: str
    role: str


class RetakeMeetingRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str
    department_id: int | None = None
    date: str
    link: str | None = None
    title: str | None = None
    retake_count: int = 0


class RetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str
    group_uuid: str
    subject_uuid: str
    subject_name: str | None = None
    date: str
    time_slots: list[int]
    room_uuid: str | None = None
    link: str | None = None
    meeting_id: str | None = None
    department_id: int | None = None
    attempt_number: int
    created_by: str | None = None
    created_at: datetime | None = None
    can_delete: bool = False
    teachers: list[RetakeTeacherRead] = Field(default_factory=list)
    meeting: RetakeMeetingRead | None = None


class GroupRetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str
    subject_uuid: str
    subject_name: str | None = None
    attempt_number: int
    date: str
    link: str | None = None
    meeting_id: str | None = None
    created_by: str | None = None
    can_delete: bool = False


class TeacherRetakeRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: str
    group_uuid: str
    subject_uuid: str
    subject_name: str | None = None
    date: str
    time_slots: list[int]
    room: str | None = None
    link: str | None = None
    attempt_number: int
    my_role: str


class GroupHistoryEntryRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    subject_name: str
    teacher_names: list[str] = Field(default_factory=list)


class RetakeSubjectOptionRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    uuid: str
    name: str


class RetakeFormContextRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    group_number: str
    group_uuid: str
    subject_uuid: str | None = None
    main_teacher_uuids: list[str] = Field(default_factory=list)
    commission_teacher_uuids: list[str] = Field(default_factory=list)
    chairman_uuid: str | None = None
    include_group_data: bool = True
    include_subject_data: bool = True
    include_teacher_data: bool = True


class RetakeFormContextRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    group_history: list[GroupHistoryEntryRead] = Field(default_factory=list)
    existing_retakes: list[GroupRetakeRead] = Field(default_factory=list)
    available_subjects: list[RetakeSubjectOptionRead] = Field(default_factory=list)
    subject_blocked_reason: str | None = None
    assigned_attempts: list[int] = Field(default_factory=list)
    next_attempt_number: int = 1
    available_main_teacher_uuids: list[str] = Field(default_factory=list)
    available_commission_teacher_uuids: list[str] = Field(default_factory=list)
    available_chairman_uuids: list[str] = Field(default_factory=list)
    available_meetings: list[RetakeMeetingRead] = Field(default_factory=list)
    department_id: int | None = None
    main_teacher_lacks_dept: bool = False


class MergedDayDetailsRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    subject: str
    type: str
    location: str


class MergedDaySlotRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    reason: str
    details: MergedDayDetailsRead


class MergedDayScheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    group_number: str
    group_uuid: str
    teacher_uuids: list[str] = Field(default_factory=list)
    date: str

    @field_validator("date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        if len(value) != 10:
            raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")
        return value


class RetakeCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    group_number: str
    group_uuid: str
    subject_uuid: str
    date: str
    time_slots: list[int]
    room_uuid: str | None = None
    link: str | None = None
    meeting_id: str | None = None
    department_id: int | None = None
    is_online: bool = False
    attempt_number: int = 1
    main_teacher_uuids: list[str]
    commission_teacher_uuids: list[str] = Field(default_factory=list)
    chairman_uuid: str | None = None

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


class RetakeMeetingUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    link: str | None = None
    title: str | None = None
