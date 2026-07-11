from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import Pagination, pagination
from app.core.database import get_db
from app.models import Merchant
from app.repositories import merchants as repo
from app.schemas.common import Page
from app.schemas.merchant import MerchantRead

router = APIRouter(prefix="/merchants", tags=["merchants"])


@router.get("", response_model=Page[MerchantRead])
def list_merchants(
    pg: Pagination = Depends(pagination),
    category: str | None = None,
    high_risk_only: bool = False,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    rows, total = repo.list_merchants(
        db,
        page=pg.page,
        page_size=pg.page_size,
        category=category,
        high_risk_only=high_risk_only,
        q=q,
    )
    return Page.build(rows, total, pg.page, pg.page_size)


@router.get("/{merchant_id}", response_model=MerchantRead)
def get_merchant(merchant_id: int, db: Session = Depends(get_db)):
    m = db.get(Merchant, merchant_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Merchant not found")
    return m
