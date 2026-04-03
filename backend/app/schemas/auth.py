from pydantic import BaseModel, ConfigDict, Field


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)


class AuthUserRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    username: str
    full_name: str = Field(serialization_alias="fullName")
    role: str
    is_active: bool = Field(serialization_alias="isActive")
    department_id: int | None = Field(default=None, serialization_alias="departmentId")
    department_ids: list[int] = Field(default_factory=list, serialization_alias="departmentIds")
    teacher_uuid: str | None = Field(default=None, serialization_alias="teacherUuid")


class AuthResponse(BaseModel):
    user: AuthUserRead


class MessageResponse(BaseModel):
    message: str
