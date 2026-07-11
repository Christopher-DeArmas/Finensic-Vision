"""Many-to-many association tables."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table

from app.core.database import Base

alert_transactions = Table(
    "alert_transactions",
    Base.metadata,
    Column("alert_id", ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "transaction_id",
        ForeignKey("transactions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

case_transactions = Table(
    "case_transactions",
    Base.metadata,
    Column("case_id", ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "transaction_id",
        ForeignKey("transactions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)
