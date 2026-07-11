"""Suspicious Activity Report (SAR) ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.case import Case


class SarReport(Base):
    __tablename__ = "sar_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    reference: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)

    summary: Mapped[str] = mapped_column(Text, nullable=False)
    customer_section: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, default=list)
    timeline: Mapped[list] = mapped_column(JSON, default=list)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    case: Mapped["Case"] = relationship(back_populates="sar_report")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SarReport {self.reference} case={self.case_id}>"
