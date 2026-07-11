"""Case lifecycle: open an investigation from an alert."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Alert, Case
from app.utils.enums import CaseStatus


class CaseService:
    @staticmethod
    def _next_case_number(db: Session) -> str:
        year = datetime.utcnow().year
        count = db.query(func.count(Case.id)).scalar() or 0
        return f"CASE-{year}-{count + 1:04d}"

    @staticmethod
    def create_from_alert(db: Session, alert_id: int) -> Case | None:
        alert = db.get(Alert, alert_id)
        if alert is None:
            return None

        # One investigation per alert: return the existing case if present.
        existing = db.query(Case).filter(Case.alert_id == alert_id).first()
        if existing is not None:
            return existing

        case = Case(
            case_number=CaseService._next_case_number(db),
            customer_id=alert.customer_id,
            alert_id=alert.id,
            title=f"Investigation: {alert.title}",
            status=CaseStatus.OPEN.value,
            priority=alert.severity,
        )
        # Carry the alert's evidence transactions into the case.
        case.transactions = list(alert.transactions)

        # Mark the alert as under review.
        alert.status = "in_review"

        db.add(case)
        db.commit()
        db.refresh(case)
        return case
