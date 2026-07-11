"""Transaction ORM model — the core event table."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.account import Account
from app.models.merchant import Merchant


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(24), unique=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    sender_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    receiver_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True
    )
    merchant_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("merchants.id", ondelete="SET NULL"), nullable=True
    )

    transaction_type: Mapped[str] = mapped_column(String(16), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(16), nullable=False)
    merchant_category: Mapped[Optional[str]] = mapped_column(String(48), nullable=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    country: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    device_id: Mapped[str] = mapped_column(String(48), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)

    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships (explicit foreign_keys because there are two FKs to accounts)
    sender_account: Mapped[Optional["Account"]] = relationship(
        foreign_keys=[sender_account_id]
    )
    receiver_account: Mapped[Optional["Account"]] = relationship(
        foreign_keys=[receiver_account_id]
    )
    merchant: Mapped[Optional["Merchant"]] = relationship(foreign_keys=[merchant_id])

    __table_args__ = (
        Index("ix_transactions_timestamp", "timestamp"),
        Index("ix_transactions_sender", "sender_account_id"),
        Index("ix_transactions_receiver", "receiver_account_id"),
        Index("ix_transactions_merchant", "merchant_id"),
        Index("ix_transactions_type", "transaction_type"),
        Index("ix_transactions_country", "country"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Transaction {self.external_id} {self.transaction_type} "
            f"{self.amount:.2f} {self.currency}>"
        )
