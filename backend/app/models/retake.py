from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Retake(Base):
    __tablename__ = "retakes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    group_uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    subject_uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)
    time_slots: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    room_uuid: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("retake_meetings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), server_default=text("now()"))

    teacher_links: Mapped[list["RetakeTeacher"]] = relationship(
        back_populates="retake",
        cascade="all, delete-orphan",
    )
    lead_teacher_links: Mapped[list["RetakeLeadTeacher"]] = relationship(
        back_populates="retake",
        cascade="all, delete-orphan",
    )
    meeting: Mapped["RetakeMeeting | None"] = relationship(back_populates="retakes")
