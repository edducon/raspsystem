from pydantic import BaseModel


class UserBase(BaseModel):
    full_name: str
    role: str
    is_active: bool = True
    department_id: int | None = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int

    model_config = {"from_attributes": True}
