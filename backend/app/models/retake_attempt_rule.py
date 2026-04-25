from __future__ import annotations

from sqlalchemy import Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RetakeAttemptRule(Base):
    __tablename__ = "retake_attempt_rules"

    attempt_number: Mapped[int] = mapped_column(Integer, primary_key=True)
    requires_chairman: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_commission_members: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
