from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: str | None = None
    title: str
    description: str
    severity: str
    score: int
    triggered_rules: list[str]
    status: str
    created_at: datetime
    transaction_count: int = 0


class AlertUpdate(BaseModel):
    status: str
