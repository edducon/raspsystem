from pydantic import BaseModel


class DepartmentBase(BaseModel):
    name: str
    short_name: str


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentRead(DepartmentBase):
    id: int

    model_config = {"from_attributes": True}
