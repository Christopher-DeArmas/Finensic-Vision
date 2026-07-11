"""Customer-to-customer relationship ORM model (powers the graph)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Relationship(Base):
    __tablename__ = "relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    target_customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(String(16), nullable=False)
    strength: Mapped[float] = mapped_column(Float, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_relationships_source", "source_customer_id"),
        Index("ix_relationships_target", "target_customer_id"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Relationship {self.source_customer_id}->{self.target_customer_id} "
            f"({self.relationship_type})>"
        )
