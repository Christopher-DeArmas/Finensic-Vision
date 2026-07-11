"""Lightweight per-customer scoring for the live stream.

The batch ScoringService preloads the entire dataset (great for a full rescore,
too heavy per streamed transaction). This builds a context scoped to a single
customer via targeted queries and runs the same pure engine. Circular-ring
detection (which needs the global graph) is left to the batch rescore.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.data.reference import HIGH_RISK_COUNTRIES
from app.models import Account, Customer, Transaction
from app.rules.context import AccountView, CustomerView, RuleContext, TxnView
from app.rules.engine import RuleEngine, ScoreResult
from app.rules.rules import HIGH_RISK_MERCHANT_CATS
from app.utils.enums import PaymentMethod

_engine = RuleEngine()


def _resolve_counterparties(db: Session, account_ids: set[int]) -> dict[int, int]:
    """Map account_id -> customer_id for the given accounts."""
    if not account_ids:
        return {}
    rows = (
        db.query(Account.id, Account.customer_id)
        .filter(Account.id.in_(account_ids))
        .all()
    )
    return {aid: cid for aid, cid in rows}


def build_scoped_context(db: Session, customer: Customer) -> RuleContext:
    accounts = db.query(Account).filter(Account.customer_id == customer.id).all()
    acc_ids = {a.id for a in accounts}

    txns = (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.sender_account_id.in_(acc_ids),
                Transaction.receiver_account_id.in_(acc_ids),
            )
        )
        .order_by(Transaction.timestamp)
        .all()
    )

    # Resolve counterparty customers for labeling / multi-source rule.
    counterparty_accounts = set()
    for t in txns:
        if t.sender_account_id and t.sender_account_id not in acc_ids:
            counterparty_accounts.add(t.sender_account_id)
        if t.receiver_account_id and t.receiver_account_id not in acc_ids:
            counterparty_accounts.add(t.receiver_account_id)
    acc_to_cust = _resolve_counterparties(db, counterparty_accounts)

    inbound: list[TxnView] = []
    outbound: list[TxnView] = []
    located: list[TxnView] = []

    for t in txns:
        is_hr_merchant = (t.merchant_category or "") in HIGH_RISK_MERCHANT_CATS
        if t.sender_account_id in acc_ids:
            v = TxnView(
                id=t.id, external_id=t.external_id, timestamp=t.timestamp,
                amount=t.amount, transaction_type=t.transaction_type,
                payment_method=t.payment_method, direction="out",
                account_id=t.sender_account_id,
                counterparty_account_id=t.receiver_account_id,
                counterparty_customer_id=acc_to_cust.get(t.receiver_account_id),
                merchant_id=t.merchant_id, merchant_category=t.merchant_category,
                is_high_risk_merchant=is_hr_merchant, country=t.country,
                city=t.city, latitude=t.latitude, longitude=t.longitude,
            )
            outbound.append(v)
            if t.payment_method == PaymentMethod.CARD.value:
                located.append(v)
        if t.receiver_account_id in acc_ids:
            inbound.append(
                TxnView(
                    id=t.id, external_id=t.external_id, timestamp=t.timestamp,
                    amount=t.amount, transaction_type=t.transaction_type,
                    payment_method=t.payment_method, direction="in",
                    account_id=t.receiver_account_id,
                    counterparty_account_id=t.sender_account_id,
                    counterparty_customer_id=acc_to_cust.get(t.sender_account_id),
                    merchant_id=t.merchant_id, merchant_category=t.merchant_category,
                    is_high_risk_merchant=is_hr_merchant, country=t.country,
                    city=t.city, latitude=t.latitude, longitude=t.longitude,
                )
            )

    return RuleContext(
        customer=CustomerView(
            id=customer.id, full_name=customer.full_name,
            occupation=customer.occupation, country=customer.country,
            is_high_risk_jurisdiction=customer.is_high_risk_jurisdiction,
            date_opened=customer.date_opened,
            expected_monthly_income=customer.expected_monthly_income,
            expected_monthly_spend=customer.expected_monthly_spend,
        ),
        accounts=[
            AccountView(
                id=a.id, account_type=a.account_type, opened_at=a.opened_at,
                last_activity_at=a.last_activity_at, is_dormant=a.is_dormant,
            )
            for a in accounts
        ],
        account_ids=acc_ids,
        inbound=inbound,
        outbound=outbound,
        located_txns=located,
        now=datetime.utcnow(),
        high_risk_countries=set(HIGH_RISK_COUNTRIES),
        cycles=[],
        cycle_transaction_ids=[],
    )


def score_customer_scoped(db: Session, customer_id: int) -> ScoreResult | None:
    """Score one customer from scoped queries and persist the RiskScore."""
    from app.models import RiskScore

    customer = db.get(Customer, customer_id)
    if customer is None:
        return None
    ctx = build_scoped_context(db, customer)
    result = _engine.evaluate(ctx)
    db.add(
        RiskScore(
            customer_id=customer.id,
            score=result.score,
            risk_level=result.risk_level.value,
            breakdown=result.breakdown(),
        )
    )
    customer.risk_level = result.risk_level.value
    return result
