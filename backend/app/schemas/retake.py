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
            raise ValueError("Date must use YYYY-MM-DD format")
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
            raise ValueError("Date must use YYYY-MM-DD format")
        return value

    @field_validator("time_slots")
    @classmethod
    def validate_time_slots(cls, value: list[int]) -> list[int]:
        unique_slots = sorted(set(value))
        if not unique_slots:
            raise ValueError("At least one time slot is required")
        if any(slot < 1 or slot > 7 for slot in unique_slots):
            raise ValueError("Time slots must be between 1 and 7")
        return unique_slots

    @field_validator("main_teacher_uuids")
    @classmethod
    def validate_main_teachers(cls, value: list[str]) -> list[str]:
        unique_teachers = list(dict.fromkeys(value))
        if not unique_teachers:
            raise ValueError("At least one main teacher is required")
        return unique_teachers
