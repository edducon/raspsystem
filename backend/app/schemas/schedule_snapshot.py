from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScheduleSnapshotGroup(BaseModel):
    uuid: str
    number: str
    name: str | None = None


class ScheduleSnapshotSubject(BaseModel):
    uuid: str
    name: str


class ScheduleSnapshotTeacher(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uuid: str
    full_name: Annotated[str, Field(alias="fullName")]
    department_ids: Annotated[list[int], Field(default_factory=list, alias="departmentIds")]


class ScheduleSnapshotItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    group_uuid: Annotated[str, Field(alias="groupUuid")]
    subject_uuid: Annotated[str, Field(alias="subjectUuid")]
    teacher_uuids: Annotated[list[str], Field(default_factory=list, alias="teacherUuids")]
    weekday: int
    slot: int
    subject_type: Annotated[str | None, Field(default=None, alias="subjectType")]
    location: str | None = None
    room: str | None = None
    link: str | None = None
    start_date: Annotated[str | None, Field(default=None, alias="startDate")]
    end_date: Annotated[str | None, Field(default=None, alias="endDate")]

    @field_validator("teacher_uuids")
    @classmethod
    def validate_teacher_uuids(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(uuid for uuid in value if uuid))

    @field_validator("weekday")
    @classmethod
    def validate_weekday(cls, value: int) -> int:
        if value < 1 or value > 7:
            raise ValueError("День недели должен быть в диапазоне от 1 до 7.")
        return value

    @field_validator("slot")
    @classmethod
    def validate_slot(cls, value: int) -> int:
        if value < 1 or value > 7:
            raise ValueError("Номер пары должен быть в диапазоне от 1 до 7.")
        return value

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_optional_date(cls, value: str | None) -> str | None:
        if value is None or len(value) == 10:
            return value
        raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД.")


class ScheduleSnapshotBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    semester_label: Annotated[str, Field(alias="semesterLabel")]
    status: str = "draft"
    source_type: Annotated[str, Field(default="raspyx", alias="sourceType")]
    description: str | None = None
    is_reference_for_retakes: Annotated[bool, Field(default=False, alias="isReferenceForRetakes")]
    captured_at: Annotated[datetime | None, Field(default=None, alias="capturedAt")]
    groups: list[ScheduleSnapshotGroup] = Field(default_factory=list)
    subjects: list[ScheduleSnapshotSubject] = Field(default_factory=list)
    teachers: list[ScheduleSnapshotTeacher] = Field(default_factory=list)
    schedule_items: Annotated[list[ScheduleSnapshotItem], Field(default_factory=list, alias="scheduleItems")]


class ScheduleSnapshotCreate(ScheduleSnapshotBase):
    pass


class ScheduleSnapshotListRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    semester_label: Annotated[str, Field(alias="semesterLabel")]
    status: str
    source_type: Annotated[str, Field(alias="sourceType")]
    description: str | None = None
    is_reference_for_retakes: Annotated[bool, Field(alias="isReferenceForRetakes")]
    captured_at: Annotated[datetime | None, Field(default=None, alias="capturedAt")]
    created_at: Annotated[datetime, Field(alias="createdAt")]
    group_count: Annotated[int, Field(default=0, alias="groupCount")]
    subject_count: Annotated[int, Field(default=0, alias="subjectCount")]
    teacher_count: Annotated[int, Field(default=0, alias="teacherCount")]
    schedule_item_count: Annotated[int, Field(default=0, alias="scheduleItemCount")]


class ScheduleSnapshotRead(ScheduleSnapshotBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    created_at: Annotated[datetime, Field(alias="createdAt")]
    group_count: Annotated[int, Field(default=0, alias="groupCount")]
    subject_count: Annotated[int, Field(default=0, alias="subjectCount")]
    teacher_count: Annotated[int, Field(default=0, alias="teacherCount")]
    schedule_item_count: Annotated[int, Field(default=0, alias="scheduleItemCount")]