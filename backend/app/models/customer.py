"""Customer ORM model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Float, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.alert import Alert
    from app.models.case import Case
    from app.models.risk_score import RiskScore


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    occupation: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)

    annual_income: Mapped[float] = mapped_column(Float, nullable=False)
    expected_monthly_income: Mapped[float] = mapped_column(Float, nullable=False)
    expected_monthly_spend: Mapped[float] = mapped_column(Float, nullable=False)

    risk_level: Mapped[str] = mapped_column(String(16), default="low", nullable=False)
    kyc_status: Mapped[str] = mapped_column(String(16), default="verified", nullable=False)
    is_high_risk_jurisdiction: Mapped[bool] = mapped_column(Boolean, default=False)

    date_opened: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scenario_tag: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    risk_scores: Mapped[list["RiskScore"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    cases: Mapped[list["Case"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_customers_country", "country"),
        Index("ix_customers_risk_level", "risk_level"),
        Index("ix_customers_scenario_tag", "scenario_tag"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Customer {self.id} {self.full_name!r} risk={self.risk_level}>"
