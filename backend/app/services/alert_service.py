"""Alert creation from engine results."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Alert, Customer, Transaction
from app.rules.engine import ScoreResult
from app.utils.enums import AlertStatus

MAX_LINKED_TXNS = 50


class AlertService:
    """Turns a high-risk ``ScoreResult`` into a persisted ``Alert``."""

    @staticmethod
    def create_from_score(
        db: Session, customer: Customer, score: ScoreResult
    ) -> Alert:
        top = max(score.results, key=lambda r: r.points)
        reasons = " ".join(r.reason for r in score.results[:3])
        title = f"{top.rule_name} risk on {customer.full_name}"
        description = (
            f"Risk score {score.score}/100 ({score.risk_level.value}). "
            f"{len(score.results)} rule(s) triggered. {reasons}"
        )

        alert = Alert(
            customer_id=customer.id,
            title=title[:160],
            description=description,
            severity=score.top_severity.value,
            score=score.score,
            triggered_rules=score.triggered_rule_codes,
            status=AlertStatus.OPEN.value,
        )

        txn_ids = score.transaction_ids[:MAX_LINKED_TXNS]
        if txn_ids:
            alert.transactions = (
                db.query(Transaction).filter(Transaction.id.in_(txn_ids)).all()
            )

        db.add(alert)
        return alert
