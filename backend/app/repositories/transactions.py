"""Transaction data access with filtering + label enrichment."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Account, Customer, Merchant, Transaction
from app.schemas.transaction import TransactionRead


def enrich(db: Session, txns: list[Transaction]) -> list[TransactionRead]:
    """Attach human-readable sender/receiver/merchant labels."""
    acc_ids = {t.sender_account_id for t in txns} | {t.receiver_account_id for t in txns}
    acc_ids.discard(None)
    merch_ids = {t.merchant_id for t in txns}
    merch_ids.discard(None)

    acc_map: dict[int, str] = {}
    if acc_ids:
        rows = (
            db.query(Account.id, Customer.full_name)
            .join(Customer, Account.customer_id == Customer.id)
            .filter(Account.id.in_(acc_ids))
            .all()
        )
        acc_map = {aid: name for aid, name in rows}

    merch_map: dict[int, str] = {}
    if merch_ids:
        rows = db.query(Merchant.id, Merchant.name).filter(Merchant.id.in_(merch_ids)).all()
        merch_map = dict(rows)

    out: list[TransactionRead] = []
    for t in txns:
        r = TransactionRead.model_validate(t)
        r.sender_name = acc_map.get(t.sender_account_id)
        r.receiver_name = acc_map.get(t.receiver_account_id)
        r.merchant_name = merch_map.get(t.merchant_id)
        out.append(r)
    return out


def list_transactions(
    db: Session,
    *,
    page: int,
    page_size: int,
    customer_id: int | None = None,
    account_id: int | None = None,
    transaction_type: str | None = None,
    payment_method: str | None = None,
    merchant_category: str | None = None,
    country: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    start: date | None = None,
    end: date | None = None,
    flagged: bool | None = None,
    q: str | None = None,
) -> tuple[list[Transaction], int]:
    stmt = select(Transaction)

    if account_id is not None:
        stmt = stmt.where(
            (Transaction.sender_account_id == account_id)
            | (Transaction.receiver_account_id == account_id)
        )
    if customer_id is not None:
        acc_ids = [
            a.id for a in db.query(Account.id).filter(Account.customer_id == customer_id)
        ]
        acc_ids = [a[0] if isinstance(a, tuple) else a for a in acc_ids]
        stmt = stmt.where(
            Transaction.sender_account_id.in_(acc_ids)
            | Transaction.receiver_account_id.in_(acc_ids)
        )
    if transaction_type:
        stmt = stmt.where(Transaction.transaction_type == transaction_type)
    if payment_method:
        stmt = stmt.where(Transaction.payment_method == payment_method)
    if merchant_category:
        stmt = stmt.where(Transaction.merchant_category == merchant_category)
    if country:
        stmt = stmt.where(Transaction.country == country)
    if min_amount is not None:
        stmt = stmt.where(Transaction.amount >= min_amount)
    if max_amount is not None:
        stmt = stmt.where(Transaction.amount <= max_amount)
    if start is not None:
        stmt = stmt.where(Transaction.timestamp >= datetime.combine(start, time.min))
    if end is not None:
        stmt = stmt.where(Transaction.timestamp <= datetime.combine(end, time.max))
    if flagged is not None:
        stmt = stmt.where(Transaction.is_flagged == flagged)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            Transaction.external_id.ilike(like) | Transaction.city.ilike(like)
        )

    total = db.scalar(select(_count()).select_from(stmt.subquery()))
    rows = (
        db.execute(
            stmt.order_by(Transaction.timestamp.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    return rows, int(total or 0)


def _count():
    from sqlalchemy import func

    return func.count()
