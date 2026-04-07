from datetime import datetime
from typing import Any, Annotated

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    created_at: Annotated[datetime, Field(serialization_alias="createdAt")]
    actor_user_id: Annotated[int | None, Field(default=None, serialization_alias="actorUserId")]
    action: str
    target_type: Annotated[str | None, Field(default=None, serialization_alias="targetType")]
    target_id: Annotated[str | None, Field(default=None, serialization_alias="targetId")]
    status: str
    ip_address: Annotated[str | None, Field(default=None, serialization_alias="ipAddress")]
    user_agent: Annotated[str | None, Field(default=None, serialization_alias="userAgent")]
    details: dict[str, Any] | None = None


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    total: int
    limit: int
    offset: int
