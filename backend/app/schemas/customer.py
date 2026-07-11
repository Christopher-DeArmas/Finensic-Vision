from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.account import AccountRead
from app.schemas.risk_score import RiskScoreRead


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    occupation: str
    country: str
    city: str
    risk_level: str
    kyc_status: str
    is_high_risk_jurisdiction: bool
    scenario_tag: str | None
    risk_score: int | None = None


class CustomerDetail(CustomerSummary):
    annual_income: float
    expected_monthly_income: float
    expected_monthly_spend: float
    date_opened: datetime
    accounts: list[AccountRead] = []
    latest_risk: RiskScoreRead | None = None
