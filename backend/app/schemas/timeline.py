from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    id: str
    type: str  # account_opened | transaction | alert | case_opened
    timestamp: datetime
    title: str
    description: str | None = None
    severity: str | None = None
    amount: float | None = None
    flagged: bool = False
