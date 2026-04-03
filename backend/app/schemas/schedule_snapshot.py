from datetime import datetime

from pydantic import BaseModel


class ScheduleSnapshotBase(BaseModel):
    name: str
    semester_label: str
    status: str = "draft"
    source_type: str = "raspyx"
    description: str | None = None
    is_reference_for_retakes: bool = False
    captured_at: datetime | None = None


class ScheduleSnapshotCreate(ScheduleSnapshotBase):
    pass


class ScheduleSnapshotRead(ScheduleSnapshotBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
