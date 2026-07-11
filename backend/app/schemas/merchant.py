from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MerchantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    country: str
    city: str
    mcc: str
    is_high_risk: bool
