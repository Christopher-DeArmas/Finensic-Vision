from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseCreate(BaseModel):
    alert_id: int


class CaseUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    analyst_notes: str | None = None


class CaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    customer_id: int
    customer_name: str | None = None
    alert_id: int | None
    title: str
    status: str
    priority: str
    ai_summary: dict | None
    analyst_notes: str | None
    opened_at: datetime
    closed_at: datetime | None
    transaction_count: int = 0
    has_sar: bool = False
