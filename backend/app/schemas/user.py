from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

UserRole = Literal["ADMIN", "EMPLOYEE", "TEACHER"]


class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole
    is_active: bool = True
    department_id: int | None = None
    department_ids: list[int] = Field(default_factory=list)
    teacher_uuid: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    password: str | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    full_name: Annotated[str, Field(serialization_alias="fullName")]
    is_active: Annotated[bool, Field(serialization_alias="isActive")]
    department_id: Annotated[int | None, Field(default=None, serialization_alias="departmentId")]
    department_ids: Annotated[list[int], Field(default_factory=list, serialization_alias="departmentIds")]
    teacher_uuid: Annotated[str | None, Field(default=None, serialization_alias="teacherUuid")]