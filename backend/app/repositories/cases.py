"""Case data access."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Case, Customer
from app.schemas.case import CaseRead


def _to_read(db: Session, cases: list[Case]) -> list[CaseRead]:
    cust_ids = {c.customer_id for c in cases}
    names = {}
    if cust_ids:
        rows = db.query(Customer.id, Customer.full_name).filter(Customer.id.in_(cust_ids)).all()
        names = dict(rows)
    out = []
    for c in cases:
        r = CaseRead.model_validate(c)
        r.customer_name = names.get(c.customer_id)
        r.transaction_count = len(c.transactions)
        out.append(r)
    return out


def list_cases(
    db: Session,
    *,
    page: int,
    page_size: int,
    status: str | None = None,
    priority: str | None = None,
) -> tuple[list[CaseRead], int]:
    stmt = select(Case)
    if status:
        stmt = stmt.where(Case.status == status)
    if priority:
        stmt = stmt.where(Case.priority == priority)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (
        db.execute(stmt.order_by(Case.opened_at.desc()).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return _to_read(db, rows), int(total or 0)


def get_case(db: Session, case_id: int) -> CaseRead | None:
    c = db.get(Case, case_id)
    if c is None:
        return None
    return _to_read(db, [c])[0]


def for_customer(db: Session, customer_id: int) -> list[CaseRead]:
    rows = (
        db.query(Case)
        .filter(Case.customer_id == customer_id)
        .order_by(Case.opened_at.desc())
        .all()
    )
    return _to_read(db, rows)
