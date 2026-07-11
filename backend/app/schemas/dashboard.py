from __future__ import annotations

from pydantic import BaseModel

from app.schemas.alert import AlertRead
from app.schemas.customer import CustomerSummary


class HeatPoint(BaseModel):
    latitude: float
    longitude: float
    amount: float
    country: str
    is_flagged: bool
    label: str | None = None


class RegionStat(BaseModel):
    region: str
    count: int
    amount: float


class DashboardStats(BaseModel):
    total_customers: int
    total_accounts: int
    total_transactions: int
    todays_transactions: int
    open_cases: int
    critical_cases: int
    closed_cases: int
    open_alerts: int
    risk_distribution: dict[str, int]
    top_risk_customers: list[CustomerSummary]
    recent_alerts: list[AlertRead]
    heatmap: list[HeatPoint]
    top_regions: list[RegionStat]
