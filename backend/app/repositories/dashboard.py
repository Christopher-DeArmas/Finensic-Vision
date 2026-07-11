"""Aggregations for the dashboard landing page."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Account, Alert, Case, Customer, Transaction
from app.schemas.dashboard import HeatPoint


def counts(db: Session) -> dict:
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    return {
        "total_customers": db.query(func.count(Customer.id)).scalar() or 0,
        "total_accounts": db.query(func.count(Account.id)).scalar() or 0,
        "total_transactions": db.query(func.count(Transaction.id)).scalar() or 0,
        "todays_transactions": db.query(func.count(Transaction.id))
        .filter(Transaction.timestamp >= day_ago)
        .scalar()
        or 0,
        "open_cases": db.query(func.count(Case.id))
        .filter(Case.status.in_(["open", "investigating"]))
        .scalar()
        or 0,
        "critical_cases": db.query(func.count(Case.id))
        .filter(Case.priority == "critical")
        .scalar()
        or 0,
        "open_alerts": db.query(func.count(Alert.id))
        .filter(Alert.status == "open")
        .scalar()
        or 0,
    }


def risk_distribution(db: Session) -> dict[str, int]:
    dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    rows = (
        db.query(Customer.risk_level, func.count(Customer.id))
        .group_by(Customer.risk_level)
        .all()
    )
    for level, count in rows:
        if level in dist:
            dist[level] = count
    return dist


def heatmap(db: Session, limit: int = 400) -> list[HeatPoint]:
    # Prioritize flagged transactions, then fill with recent ones.
    rows = (
        db.query(Transaction)
        .order_by(Transaction.is_flagged.desc(), Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        HeatPoint(
            latitude=t.latitude,
            longitude=t.longitude,
            amount=t.amount,
            country=t.country,
            is_flagged=t.is_flagged,
        )
        for t in rows
    ]
