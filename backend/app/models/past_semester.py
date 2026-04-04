from __future__ import annotations

from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PastSemester(Base):
    __tablename__ = "past_semester"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    group_name: Mapped[str] = mapped_column(String(255), index=True)
    subject_name: Mapped[str] = mapped_column(Text)
    teacher_names: Mapped[list[str]] = mapped_column(ARRAY(Text))
    date_range_start: Mapped[str | None] = mapped_column(String(10), nullable=True)
    date_range_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
