"""Merchant data access."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Merchant


def list_merchants(
    db: Session,
    *,
    page: int,
    page_size: int,
    category: str | None = None,
    high_risk_only: bool = False,
    q: str | None = None,
) -> tuple[list[Merchant], int]:
    stmt = select(Merchant)
    if category:
        stmt = stmt.where(Merchant.category == category)
    if high_risk_only:
        stmt = stmt.where(Merchant.is_high_risk.is_(True))
    if q:
        stmt = stmt.where(Merchant.name.ilike(f"%{q}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (
        db.execute(stmt.order_by(Merchant.name).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return rows, int(total or 0)
