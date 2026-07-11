"""Aggregations for the dashboard landing page."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Account, Alert, Case, Customer, Transaction
from app.schemas.dashboard import HeatPoint, RegionStat

# Group countries into broad world regions for the "risky regions" chart.
COUNTRY_REGION: dict[str, str] = {
    "United States": "North America",
    "Panama": "North America",
    "Cayman Islands": "North America",
    "United Kingdom": "Europe",
    "Germany": "Europe",
    "Switzerland": "Europe",
    "Malta": "Europe",
    "Cyprus": "Europe",
    "Russia": "Europe",
    "Singapore": "Asia",
    "Hong Kong": "Asia",
    "Japan": "Asia",
    "United Arab Emirates": "Middle East",
    "Nigeria": "Africa",
    "Canada": "North America",
    "Mexico": "North America",
    "Brazil": "South America",
    "France": "Europe",
    "Netherlands": "Europe",
    "Spain": "Europe",
    "Italy": "Europe",
    "Sweden": "Europe",
    "India": "Asia",
    "South Korea": "Asia",
    "China": "Asia",
    "Australia": "Oceania",
    "South Africa": "Africa",
}


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
        "closed_cases": db.query(func.count(Case.id))
        .filter(Case.status == "closed")
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


def top_regions(db: Session) -> list[RegionStat]:
    day_ago = datetime.utcnow() - timedelta(days=1)
    rows = (
        db.query(
            Transaction.country,
            func.count(Transaction.id),
            func.coalesce(func.sum(Transaction.amount), 0.0),
        )
        .filter(Transaction.is_flagged.is_(True), Transaction.timestamp >= day_ago)
        .group_by(Transaction.country)
        .all()
    )
    agg: dict[str, list[float]] = {}
    for country, cnt, amt in rows:
        region = COUNTRY_REGION.get(country, "Other")
        cur = agg.setdefault(region, [0, 0.0])
        cur[0] += cnt
        cur[1] += float(amt or 0)
    return [
        RegionStat(region=r, count=int(v[0]), amount=round(v[1], 2))
        for r, v in sorted(agg.items(), key=lambda kv: kv[1][0], reverse=True)
    ][:5]


def heatmap(db: Session, limit: int = 400) -> list[HeatPoint]:
    rows = (
        db.query(Transaction)
        .order_by(Transaction.is_flagged.desc(), Transaction.timestamp.desc())
        .limit(limit)
        .all()
    )
    # Resolve the associated customer name for hover labels.
    acc_ids = set()
    for t in rows:
        acc_ids.add(t.sender_account_id or t.receiver_account_id)
    acc_ids.discard(None)
    names: dict[int, str] = {}
    if acc_ids:
        for aid, name in (
            db.query(Account.id, Customer.full_name)
            .join(Customer, Account.customer_id == Customer.id)
            .filter(Account.id.in_(acc_ids))
        ):
            names[aid] = name

    points = []
    for t in rows:
        aid = t.sender_account_id or t.receiver_account_id
        points.append(
            HeatPoint(
                latitude=t.latitude,
                longitude=t.longitude,
                amount=t.amount,
                country=t.country,
                is_flagged=t.is_flagged,
                label=names.get(aid),
            )
        )
    return points
