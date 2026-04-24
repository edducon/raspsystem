from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RetakeLeadTeacher(Base):
    __tablename__ = "retake_lead_teachers"

    retake_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("retakes.id", ondelete="CASCADE"),
        primary_key=True,
    )
    teacher_uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("teachers_local.uuid"),
        primary_key=True,
    )

    retake: Mapped["Retake"] = relationship(back_populates="lead_teacher_links")
    teacher: Mapped["TeacherLocal"] = relationship()
