from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeacherDirectoryBase(BaseModel):
    full_name: str
    department_ids: list[int] = Field(default_factory=list)
    position_id: int | None = None


class TeacherDirectoryCreate(TeacherDirectoryBase):
    uuid: UUID | None = None


class TeacherDirectoryUpdate(TeacherDirectoryBase):
    pass


class TeacherDirectoryRead(TeacherDirectoryBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    uuid: str
    full_name: Annotated[str, Field(serialization_alias="fullName")]
    department_ids: Annotated[list[int], Field(default_factory=list, serialization_alias="departmentIds")]
    position_id: Annotated[int | None, Field(default=None, serialization_alias="positionId")]
