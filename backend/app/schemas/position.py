from pydantic import BaseModel


class PositionBase(BaseModel):
    name: str
    sort_order: int = 0
    is_active: bool = True


class PositionCreate(PositionBase):
    pass


class PositionRead(PositionBase):
    id: int

    model_config = {"from_attributes": True}
