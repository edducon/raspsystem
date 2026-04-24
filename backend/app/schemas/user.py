from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

UserRole = Literal["ADMIN", "EMPLOYEE", "TEACHER", "SERVICE"]


class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole
    is_active: bool = True
    must_change_password: bool = False
    can_schedule_semester: bool = False
    can_schedule_session: bool = False
    can_schedule_retakes: bool = False
    department_id: int | None = None
    department_ids: list[int] = Field(default_factory=list)
    teacher_uuid: str | None = None


class UserCreate(UserBase):
    password: str


class UserUpdate(UserBase):
    must_change_password: bool | None = None
    can_schedule_semester: bool | None = None
    can_schedule_session: bool | None = None
    can_schedule_retakes: bool | None = None
    password: str | None = None


class UserSchedulePermissionsUpdate(BaseModel):
    can_schedule_semester: bool | None = None
    can_schedule_session: bool | None = None
    can_schedule_retakes: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    full_name: Annotated[str, Field(serialization_alias="fullName")]
    is_active: Annotated[bool, Field(serialization_alias="isActive")]
    must_change_password: Annotated[bool, Field(default=False, serialization_alias="mustChangePassword")]
    can_schedule_semester: Annotated[bool, Field(default=False, serialization_alias="canScheduleSemester")]
    can_schedule_session: Annotated[bool, Field(default=False, serialization_alias="canScheduleSession")]
    can_schedule_retakes: Annotated[bool, Field(default=False, serialization_alias="canScheduleRetakes")]
    department_id: Annotated[int | None, Field(default=None, serialization_alias="departmentId")]
    department_ids: Annotated[list[int], Field(default_factory=list, serialization_alias="departmentIds")]
    teacher_uuid: Annotated[str | None, Field(default=None, serialization_alias="teacherUuid")]
