from pydantic import BaseModel


class TeacherBase(BaseModel):
    full_name: str
    department_id: int
    position_id: int | None = None


class TeacherCreate(TeacherBase):
    pass


class TeacherRead(TeacherBase):
    id: int

    model_config = {"from_attributes": True}
