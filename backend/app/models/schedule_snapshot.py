from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScheduleSnapshot(Base):
    __tablename__ = "schedule_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    semester_label: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    source_type: Mapped[str] = mapped_column(String(50), default="raspyx")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_reference_for_retakes: Mapped[bool] = mapped_column(Boolean, default=False)
    groups: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    subjects: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    teachers: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    schedule_items: Mapped[list[dict]] = mapped_column(JSONB, default=list)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
