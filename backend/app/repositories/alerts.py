"""Alert data access with filters."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, func, select
from sqlalchemy.orm import Session

from app.models import Alert, Customer
from app.schemas.alert import AlertRead

_SEVERITY_BONUS = {"critical": 18.0, "high": 10.0, "medium": 4.0, "low": 0.0}
_STATUS_ADJ = {"open": 6.0, "in_review": 3.0, "escalated": 5.0, "dismissed": -40.0}


def _triage(a: Alert) -> tuple[float, dict]:
    """Composite triage priority so analysts work the highest-risk alerts first.

    Blends the raw rule score with severity, corroboration (how many rules
    agree), recency and disposition into a single 0-100 priority. Every
    component is returned so the UI can explain *why* an alert ranks where it
    does.
    """
    base = 0.55 * float(a.score)
    severity = _SEVERITY_BONUS.get(a.severity, 0.0)
    n_rules = len(a.triggered_rules or [])
    corroboration = min(12.0, max(0, n_rules - 1) * 4.0)

    age_h = max(0.0, (datetime.utcnow() - a.created_at).total_seconds() / 3600.0) if a.created_at else 0.0
    recency = round(max(0.0, 8.0 - age_h / 6.0), 1)  # up to +8 for fresh alerts

    status_adj = _STATUS_ADJ.get(a.status, 0.0)

    total = base + severity + corroboration + recency + status_adj
    total = round(max(0.0, min(100.0, total)), 1)
    factors = {
        "base_score": round(base, 1),
        "severity": severity,
        "corroboration": corroboration,
        "recency": recency,
        "status": status_adj,
    }
    return total, factors


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
        r.triage_score, r.triage_factors = _triage(a)
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
    sort: str = "triage",
) -> tuple[list[AlertRead], int]:
    stmt = select(Alert)
    if severity:
        stmt = stmt.where(Alert.severity == severity)
    if status:
        stmt = stmt.where(Alert.status == status)
    if rule:
        # triggered_rules is stored as a JSON array of strings.
        stmt = stmt.where(Alert.triggered_rules.cast(String).ilike(f'%"{rule}"%'))

    # Load the full filtered set so triage rank is global (not per-page), then
    # paginate in memory. The alert volume in this demo is comfortably small.
    all_alerts = db.execute(stmt).scalars().all()
    reads = _to_read(db, all_alerts)

    # Global triage rank: 1 = highest-priority alert in the filtered set. Uses
    # the same tie-break as the triage display sort so ranks stay monotonic.
    triage_key = lambda x: (x.triage_score, x.created_at)  # noqa: E731
    for rank, r in enumerate(
        sorted(reads, key=triage_key, reverse=True), start=1
    ):
        r.rank = rank

    if sort == "recent":
        reads.sort(key=lambda x: (x.created_at, x.id), reverse=True)
    else:  # triage (default)
        reads.sort(key=triage_key, reverse=True)

    total = len(reads)
    start = (page - 1) * page_size
    return reads[start : start + page_size], total


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
