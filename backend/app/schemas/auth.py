from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthLoginRequest(BaseModel):
    username: str
    password: str


class AuthChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 6:
            raise ValueError("Новый пароль должен содержать минимум 6 символов.")
        return value


class AuthUserRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    username: str
    full_name: Annotated[str, Field(serialization_alias="fullName")]
    role: str
    is_active: Annotated[bool, Field(serialization_alias="isActive")]
    department_id: Annotated[int | None, Field(default=None, serialization_alias="departmentId")]
    department_ids: Annotated[list[int], Field(default_factory=list, serialization_alias="departmentIds")]
    teacher_uuid: Annotated[str | None, Field(default=None, serialization_alias="teacherUuid")]


class AuthResponse(BaseModel):
    user: AuthUserRead


class MessageResponse(BaseModel):
    message: str