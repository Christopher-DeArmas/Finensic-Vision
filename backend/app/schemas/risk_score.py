from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    score: int
    risk_level: str
    breakdown: list[dict]
    computed_at: datetime
