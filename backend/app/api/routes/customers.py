from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import Pagination, pagination
from app.core.database import get_db
from app.repositories import accounts as accounts_repo
from app.repositories import customers as repo
from app.repositories import transactions as txn_repo
from app.schemas.account import AccountRead
from app.schemas.common import Page
from app.schemas.customer import CustomerDetail, CustomerSummary
from app.schemas.transaction import TransactionRead

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Page[CustomerSummary])
def list_customers(
    pg: Pagination = Depends(pagination),
    country: str | None = None,
    risk_level: str | None = None,
    kyc_status: str | None = None,
    scenario_tag: str | None = None,
    high_risk_only: bool = False,
    q: str | None = Query(None, description="Search by name"),
    db: Session = Depends(get_db),
):
    items, total = repo.list_customers(
        db,
        page=pg.page,
        page_size=pg.page_size,
        country=country,
        risk_level=risk_level,
        kyc_status=kyc_status,
        scenario_tag=scenario_tag,
        high_risk_only=high_risk_only,
        q=q,
    )
    return Page.build(items, total, pg.page, pg.page_size)


@router.get("/{customer_id}", response_model=CustomerDetail)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    detail = repo.get_customer(db, customer_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return detail


@router.get("/{customer_id}/accounts", response_model=list[AccountRead])
def customer_accounts(customer_id: int, db: Session = Depends(get_db)):
    return accounts_repo.list_for_customer(db, customer_id)


@router.get("/{customer_id}/transactions", response_model=Page[TransactionRead])
def customer_transactions(
    customer_id: int,
    pg: Pagination = Depends(pagination),
    db: Session = Depends(get_db),
):
    rows, total = txn_repo.list_transactions(
        db, page=pg.page, page_size=pg.page_size, customer_id=customer_id
    )
    return Page.build(txn_repo.enrich(db, rows), total, pg.page, pg.page_size)
