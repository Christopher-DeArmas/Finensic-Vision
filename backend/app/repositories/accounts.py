"""Account data access."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Account


def get_account(db: Session, account_id: int) -> Account | None:
    return db.get(Account, account_id)


def list_for_customer(db: Session, customer_id: int) -> list[Account]:
    return db.query(Account).filter(Account.customer_id == customer_id).all()
