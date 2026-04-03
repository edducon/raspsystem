from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TeacherLocal(Base):
    __tablename__ = "teachers_local"

    uuid: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), index=True)
    department_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), default=list, nullable=True)

    retake_links: Mapped[list["RetakeTeacher"]] = relationship(back_populates="teacher")
