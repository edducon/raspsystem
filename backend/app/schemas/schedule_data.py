from pydantic import BaseModel, ConfigDict, Field


class GroupDictionaryRead(BaseModel):
    uuid: str
    number: str


class SubjectDictionaryRead(BaseModel):
    uuid: str
    name: str


class ScheduleDictionariesRead(BaseModel):
    groups: list[GroupDictionaryRead] = Field(default_factory=list)
    subjects: list[SubjectDictionaryRead] = Field(default_factory=list)


class TeacherScheduleRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    teacher_uuid: str = Field(serialization_alias="teacherUuid")
    teacher_full_name: str = Field(serialization_alias="teacherFullName")
    schedule: dict[str, object] = Field(default_factory=dict)
