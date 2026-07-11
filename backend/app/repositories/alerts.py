"""Alert data access with filters."""

from __future__ import annotations

from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from app.models import Alert, Customer
from app.schemas.alert import AlertRead


def _to_read(db: Session, alerts: list[Alert]) -> list[AlertRead]:
    cust_ids = {a.customer_id for a in alerts}
    names = {}
    if cust_ids:
        rows = db.query(Customer.id, Customer.full_name).filter(Customer.id.in_(cust_ids)).all()
        names = dict(rows)
    out = []
    for a in alerts:
        r = AlertRead.model_validate(a)
        r.customer_name = names.get(a.customer_id)
        r.transaction_count = len(a.transactions)
        out.append(r)
    return out


def list_alerts(
    db: Session,
    *,
    page: int,
    page_size: int,
    severity: str | None = None,
    status: str | None = None,
    rule: str | None = None,
) -> tuple[list[AlertRead], int]:
    stmt = select(Alert)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if status:
        stmt = stmt.where(Alert.status == status)
    if rule:
        # triggered_rules is stored as a JSON array of strings.
        stmt = stmt.where(Alert.triggered_rules.cast(String).ilike(f'%"{rule}"%'))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = (
        db.execute(
            stmt.order_by(Alert.created_at.desc(), Alert.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return _to_read(db, rows), int(total or 0)


def get_alert(db: Session, alert_id: int) -> AlertRead | None:
    a = db.get(Alert, alert_id)
    if a is None:
        return None
    return _to_read(db, [a])[0]


def recent(db: Session, limit: int = 8) -> list[AlertRead]:
    rows = (
        db.query(Alert)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .limit(limit)
        .all()
    )
    return _to_read(db, rows)


def for_customer(db: Session, customer_id: int) -> list[AlertRead]:
    rows = (
        db.query(Alert)
        .filter(Alert.customer_id == customer_id)
        .order_by(Alert.created_at.desc(), Alert.id.desc())
        .all()
    )
    return _to_read(db, rows)
