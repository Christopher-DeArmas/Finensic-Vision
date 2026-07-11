from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import alerts as alerts_repo
from app.repositories import customers as customers_repo
from app.repositories import dashboard as repo
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    c = repo.counts(db)
    return DashboardStats(
        total_customers=c["total_customers"],
        total_accounts=c["total_accounts"],
        total_transactions=c["total_transactions"],
        todays_transactions=c["todays_transactions"],
        open_cases=c["open_cases"],
        critical_cases=c["critical_cases"],
        open_alerts=c["open_alerts"],
        risk_distribution=repo.risk_distribution(db),
        top_risk_customers=customers_repo.top_risk(db, limit=8),
        recent_alerts=alerts_repo.recent(db, limit=8),
        heatmap=repo.heatmap(db),
        top_regions=repo.top_regions(db),
    )
