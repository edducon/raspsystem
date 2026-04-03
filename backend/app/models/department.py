from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    short_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

    teachers: Mapped[list["Teacher"]] = relationship(back_populates="department")
    users: Mapped[list["User"]] = relationship(back_populates="department")
