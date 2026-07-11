"""Alert ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.associations import alert_transactions

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.transaction import Transaction


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)

    # List of triggered rule codes/names.
    triggered_rules: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    customer: Mapped["Customer"] = relationship(back_populates="alerts")
    transactions: Mapped[list["Transaction"]] = relationship(
        secondary=alert_transactions
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Alert {self.id} {self.severity} score={self.score}>"
