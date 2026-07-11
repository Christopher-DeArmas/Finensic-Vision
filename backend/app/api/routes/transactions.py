from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import Pagination, pagination
from app.core.database import get_db
from app.models import Transaction
from app.repositories import transactions as repo
from app.schemas.common import Page
from app.schemas.transaction import TransactionRead

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=Page[TransactionRead])
def list_transactions(
    pg: Pagination = Depends(pagination),
    customer_id: int | None = None,
    account_id: int | None = None,
    transaction_type: str | None = None,
    payment_method: str | None = None,
    merchant_category: str | None = None,
    country: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    start: date | None = Query(None, description="Inclusive start date"),
    end: date | None = Query(None, description="Inclusive end date"),
    flagged: bool | None = None,
    q: str | None = Query(None, description="Search by reference or city"),
    db: Session = Depends(get_db),
):
    rows, total = repo.list_transactions(
        db,
        page=pg.page,
        page_size=pg.page_size,
        customer_id=customer_id,
        account_id=account_id,
        transaction_type=transaction_type,
        payment_method=payment_method,
        merchant_category=merchant_category,
        country=country,
        min_amount=min_amount,
        max_amount=max_amount,
        start=start,
        end=end,
        flagged=flagged,
        q=q,
    )
    return Page.build(repo.enrich(db, rows), total, pg.page, pg.page_size)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return repo.enrich(db, [t])[0]
