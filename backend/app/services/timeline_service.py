"""Builds a chronological timeline of an investigation's key events."""

from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Account, Alert, Case, Customer, Transaction
from app.schemas.timeline import TimelineEvent

MAX_TXN_EVENTS = 15


def build_timeline(db: Session, customer_id: int) -> list[TimelineEvent]:
    customer = db.get(Customer, customer_id)
    if customer is None:
        return []

    events: list[TimelineEvent] = []
    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    acc_ids = {a.id for a in accounts}

    # Account opened.
    opened = min((a.opened_at for a in accounts), default=customer.date_opened)
    events.append(
        TimelineEvent(
            id="acct-open",
            type="account_opened",
            timestamp=opened,
            title="Account relationship opened",
            description=f"{customer.full_name} onboarded ({customer.kyc_status}).",
        )
    )

    # Flagged transactions (the story), most recent first, capped.
    if acc_ids:
        flagged = (
            db.query(Transaction)
            .filter(
                Transaction.is_flagged.is_(True),
                or_(
                    Transaction.sender_account_id.in_(acc_ids),
                    Transaction.receiver_account_id.in_(acc_ids),
                ),
            )
            .order_by(Transaction.timestamp.desc())
            .limit(MAX_TXN_EVENTS)
            .all()
        )
        for t in flagged:
            events.append(
                TimelineEvent(
                    id=f"txn-{t.id}",
                    type="transaction",
                    timestamp=t.timestamp,
                    title=f"Flagged {t.transaction_type} · {t.city}",
                    description=f"{t.payment_method.upper()} · {t.external_id}",
                    amount=t.amount,
                    flagged=True,
                )
            )

    # Alerts.
    for a in db.query(Alert).filter(Alert.customer_id == customer_id):
        events.append(
            TimelineEvent(
                id=f"alert-{a.id}",
                type="alert",
                timestamp=a.created_at,
                title=a.title,
                description=", ".join(a.triggered_rules),
                severity=a.severity,
            )
        )

    # Cases.
    for c in db.query(Case).filter(Case.customer_id == customer_id):
        events.append(
            TimelineEvent(
                id=f"case-{c.id}",
                type="case_opened",
                timestamp=c.opened_at,
                title=f"Investigation opened · {c.case_number}",
                description=f"Priority {c.priority}",
                severity=c.priority,
            )
        )

    events.sort(key=lambda e: e.timestamp)
    return events
