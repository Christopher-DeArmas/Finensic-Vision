from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    account_number: str
    account_type: str
    currency: str
    balance: float
    opened_at: datetime
    last_activity_at: datetime | None
    is_dormant: bool
