from pydantic import BaseModel, ConfigDict, Field


class TeacherDirectoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    uuid: str
    full_name: str = Field(serialization_alias="fullName")
    department_ids: list[int] = Field(default_factory=list, serialization_alias="departmentIds")
