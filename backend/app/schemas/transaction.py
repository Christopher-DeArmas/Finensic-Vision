from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    external_id: str
    timestamp: datetime
    transaction_type: str
    payment_method: str
    amount: float
    currency: str
    country: str
    city: str
    latitude: float
    longitude: float
    merchant_category: str | None
    sender_account_id: int | None
    receiver_account_id: int | None
    merchant_id: int | None
    is_flagged: bool
    # Enriched, human-readable labels (populated by the repository).
    sender_name: str | None = None
    receiver_name: str | None = None
    merchant_name: str | None = None
