from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RetakeTeacher(Base):
    __tablename__ = "retake_teachers"

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
    role: Mapped[str] = mapped_column(String(32))

    retake: Mapped["Retake"] = relationship(back_populates="teacher_links")
    teacher: Mapped["TeacherLocal"] = relationship(back_populates="retake_links")
