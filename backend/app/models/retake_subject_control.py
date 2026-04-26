from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RetakeSubjectControl(Base):
    __tablename__ = "retake_subject_controls"
    __table_args__ = (
        UniqueConstraint("group_uuid", "subject_key", name="uq_retake_subject_controls_group_subject"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    group_number: Mapped[str] = mapped_column(String(50), index=True)
    group_family_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    subject_key: Mapped[str] = mapped_column(String(255), index=True)
    subject_name: Mapped[str] = mapped_column(Text)
    control_type: Mapped[str] = mapped_column(String(32), default="unspecified", index=True)
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), server_default=text("now()"), onupdate=text("now()"))
