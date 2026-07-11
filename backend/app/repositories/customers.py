"""Customer data access with filtering + latest-score attachment."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Customer, RiskScore
from app.schemas.customer import CustomerDetail, CustomerSummary
from app.schemas.risk_score import RiskScoreRead


def _latest_scores(db: Session, customer_ids: list[int]) -> dict[int, RiskScore]:
    if not customer_ids:
        return {}
    # Latest RiskScore per customer = max(id) per customer.
    sub = (
        db.query(func.max(RiskScore.id))
        .filter(RiskScore.customer_id.in_(customer_ids))
        .group_by(RiskScore.customer_id)
    )
    latest_ids = [row[0] for row in sub.all()]
    rows = db.query(RiskScore).filter(RiskScore.id.in_(latest_ids)).all()
    return {r.customer_id: r for r in rows}


def list_customers(
    db: Session,
    *,
    page: int,
    page_size: int,
    country: str | None = None,
    risk_level: str | None = None,
    kyc_status: str | None = None,
    scenario_tag: str | None = None,
    high_risk_only: bool = False,
    q: str | None = None,
) -> tuple[list[CustomerSummary], int]:
    stmt = select(Customer)
    if country:
        stmt = stmt.where(Customer.country == country)
    if risk_level:
        stmt = stmt.where(Customer.risk_level == risk_level)
    if kyc_status:
        stmt = stmt.where(Customer.kyc_status == kyc_status)
    if scenario_tag:
        stmt = stmt.where(Customer.scenario_tag == scenario_tag)
    if high_risk_only:
        stmt = stmt.where(Customer.risk_level.in_(["high", "critical"]))
    if q:
        stmt = stmt.where(Customer.full_name.ilike(f"%{q}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    customers = (
        db.execute(
            stmt.order_by(Customer.full_name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    scores = _latest_scores(db, [c.id for c in customers])
    out = []
    for c in customers:
        summary = CustomerSummary.model_validate(c)
        rs = scores.get(c.id)
        summary.risk_score = rs.score if rs else None
        out.append(summary)
    return out, int(total or 0)


def get_customer(db: Session, customer_id: int) -> CustomerDetail | None:
    c = db.get(Customer, customer_id)
    if c is None:
        return None
    detail = CustomerDetail.model_validate(c)
    scores = _latest_scores(db, [c.id])
    rs = scores.get(c.id)
    if rs:
        detail.latest_risk = RiskScoreRead.model_validate(rs)
        detail.risk_score = rs.score
    return detail


def top_risk(db: Session, limit: int = 10) -> list[CustomerSummary]:
    customers = (
        db.query(Customer)
        .filter(Customer.risk_level.in_(["high", "critical"]))
        .all()
    )
    scores = _latest_scores(db, [c.id for c in customers])
    out = []
    for c in customers:
        s = CustomerSummary.model_validate(c)
        rs = scores.get(c.id)
        s.risk_score = rs.score if rs else 0
        out.append(s)
    out.sort(key=lambda x: x.risk_score or 0, reverse=True)
    return out[:limit]
