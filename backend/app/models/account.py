"""Account ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.customer import Customer


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    account_number: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(16), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_dormant: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    customer: Mapped["Customer"] = relationship(back_populates="accounts")

    __table_args__ = (
        Index("ix_accounts_customer_id", "customer_id"),
        Index("ix_accounts_account_type", "account_type"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Account {self.account_number} ({self.account_type})>"
