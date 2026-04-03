from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str
    is_active: bool = True
    department_id: int | None = None


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int

    model_config = {"from_attributes": True}
