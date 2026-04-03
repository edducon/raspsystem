from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str
    full_name: str
    role: str
    is_active: bool = True
    department_id: int | None = None
    department_ids: list[int] = Field(default_factory=list)
    teacher_uuid: str | None = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    full_name: str = Field(serialization_alias="fullName")
    is_active: bool = Field(serialization_alias="isActive")
    department_id: int | None = Field(default=None, serialization_alias="departmentId")
    department_ids: list[int] = Field(default_factory=list, serialization_alias="departmentIds")
    teacher_uuid: str | None = Field(default=None, serialization_alias="teacherUuid")
