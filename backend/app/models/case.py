"""Investigation Case ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.associations import case_transactions

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.sar_report import SarReport
    from app.models.transaction import Transaction


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)

    # Cached AI investigation report (executive summary, findings, etc.)
    ai_summary: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    opened_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    customer: Mapped["Customer"] = relationship(back_populates="cases")
    transactions: Mapped[list["Transaction"]] = relationship(
        secondary=case_transactions
    )
    sar_report: Mapped[Optional["SarReport"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Case {self.case_number} status={self.status}>"
