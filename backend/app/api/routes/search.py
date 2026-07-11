from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Account, Customer, Merchant, Transaction

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
def search(
    q: str = Query(..., min_length=1, description="Search term"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    like = f"%{q}%"
    customers = (
        db.query(Customer).filter(Customer.full_name.ilike(like)).limit(limit).all()
    )
    accounts = (
        db.query(Account).filter(Account.account_number.ilike(like)).limit(limit).all()
    )
    merchants = db.query(Merchant).filter(Merchant.name.ilike(like)).limit(limit).all()
    transactions = (
        db.query(Transaction).filter(Transaction.external_id.ilike(like)).limit(limit).all()
    )
    return {
        "customers": [
            {"id": c.id, "name": c.full_name, "risk_level": c.risk_level}
            for c in customers
        ],
        "accounts": [
            {"id": a.id, "account_number": a.account_number, "type": a.account_type}
            for a in accounts
        ],
        "merchants": [
            {"id": m.id, "name": m.name, "category": m.category} for m in merchants
        ],
        "transactions": [
            {"id": t.id, "external_id": t.external_id, "amount": t.amount}
            for t in transactions
        ],
    }
