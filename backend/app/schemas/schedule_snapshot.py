from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel


class ScheduleSnapshotGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    uuid: str
    number: str
    name: str | None = None


class ScheduleSnapshotSubject(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    uuid: str
    name: str


class ScheduleSnapshotTeacher(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    uuid: str
    full_name: str
    department_ids: list[int] = Field(default_factory=list)


class ScheduleSnapshotItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    group_uuid: str
    subject_uuid: str
    teacher_uuids: list[str] = Field(default_factory=list)
    weekday: int
    slot: int
    subject_type: str | None = None
    location: str | None = None
    room: str | None = None
    link: str | None = None
    start_date: str | None = None
    end_date: str | None = None

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
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    name: str
    semester_label: str
    status: str = "draft"
    source_type: str = "raspyx"
    description: str | None = None
    is_reference_for_retakes: bool = False
    captured_at: datetime | None = None
    groups: list[ScheduleSnapshotGroup] = Field(default_factory=list)
    subjects: list[ScheduleSnapshotSubject] = Field(default_factory=list)
    teachers: list[ScheduleSnapshotTeacher] = Field(default_factory=list)
    schedule_items: list[ScheduleSnapshotItem] = Field(default_factory=list)


class ScheduleSnapshotCreate(ScheduleSnapshotBase):
    pass


class ScheduleSnapshotListRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int
    name: str
    semester_label: str
    status: str
    source_type: str
    description: str | None = None
    is_reference_for_retakes: bool
    captured_at: datetime | None = None
    created_at: datetime
    date_range_start: str | None = None
    date_range_end: str | None = None
    group_count: int = 0
    subject_count: int = 0
    teacher_count: int = 0
    schedule_item_count: int = 0


class ScheduleSnapshotRead(ScheduleSnapshotBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)

    id: int
    created_at: datetime
    group_count: int = 0
    subject_count: int = 0
    teacher_count: int = 0
    schedule_item_count: int = 0
