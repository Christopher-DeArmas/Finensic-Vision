"""Orchestrates AI summary + SAR generation for a case.

Builds the structured evidence context from the database, delegates to the AI
layer (OpenAI or template fallback), and persists the results.
"""

from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.ai import generate_investigation_summary, generate_sar_sections
from app.models import Account, Alert, Case, Customer, RiskScore, SarReport, Transaction
from app.services.timeline_service import build_timeline

MAX_FLAGGED = 15


def _build_context(db: Session, customer_id: int) -> dict:
    customer = db.get(Customer, customer_id)
    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    acc_ids = {a.id for a in accounts}

    latest = (
        db.query(RiskScore)
        .filter(RiskScore.customer_id == customer_id)
        .order_by(RiskScore.id.desc())
        .first()
    )
    rules = []
    if latest:
        rules = [
            {
                "code": b.get("rule"),
                "name": b.get("name"),
                "points": b.get("points"),
                "reason": b.get("reason"),
                "severity": b.get("severity"),
            }
            for b in latest.breakdown
        ]

    flagged = []
    if acc_ids:
        rows = (
            db.query(Transaction)
            .filter(
                Transaction.is_flagged.is_(True),
                or_(
                    Transaction.sender_account_id.in_(acc_ids),
                    Transaction.receiver_account_id.in_(acc_ids),
                ),
            )
            .order_by(Transaction.amount.desc())
            .limit(MAX_FLAGGED)
            .all()
        )
        flagged = [
            {
                "external_id": t.external_id,
                "type": t.transaction_type,
                "amount": t.amount,
                "city": t.city,
                "country": t.country,
                "timestamp": t.timestamp.isoformat(),
            }
            for t in rows
        ]

    total_flagged = 0
    if acc_ids:
        total_flagged = (
            db.query(func.count(Transaction.id))
            .filter(
                Transaction.is_flagged.is_(True),
                or_(
                    Transaction.sender_account_id.in_(acc_ids),
                    Transaction.receiver_account_id.in_(acc_ids),
                ),
            )
            .scalar()
            or 0
        )
    total_alerts = (
        db.query(func.count(Alert.id)).filter(Alert.customer_id == customer_id).scalar()
        or 0
    )

    timeline = [
        {"timestamp": e.timestamp.isoformat(), "event": e.title}
        for e in build_timeline(db, customer_id)
    ]

    return {
        "customer": {
            "name": customer.full_name,
            "occupation": customer.occupation,
            "country": customer.country,
            "city": customer.city,
            "kyc_status": customer.kyc_status,
            "risk_level": customer.risk_level,
            "risk_score": latest.score if latest else 0,
            "is_high_risk_jurisdiction": customer.is_high_risk_jurisdiction,
            "annual_income": customer.annual_income,
            "expected_monthly_income": customer.expected_monthly_income,
            "accounts_count": len(accounts),
        },
        "rules": rules,
        "flagged_transactions": flagged,
        "counts": {"total_flagged": total_flagged, "total_alerts": total_alerts},
        "timeline": timeline,
    }


class AIService:
    @staticmethod
    def summarize(db: Session, case_id: int) -> dict | None:
        case = db.get(Case, case_id)
        if case is None:
            return None
        customer = db.get(Customer, case.customer_id)
        context = _build_context(db, case.customer_id)
        summary = generate_investigation_summary(context)
        case.ai_summary = summary
        db.commit()
        return summary

    @staticmethod
    def _reference(db: Session, customer: Customer) -> str:
        """firstName-lastName-year-sequence, e.g. Paul-Castaneda-2026-0001."""
        parts = [p for p in re.sub(r"[^A-Za-z ]", "", customer.full_name).split() if p]
        first = parts[0] if parts else "Customer"
        last = parts[-1] if len(parts) > 1 else ""
        name = f"{first}-{last}" if last else first
        seq = (db.query(func.count(SarReport.id)).scalar() or 0) + 1
        return f"{name}-{datetime.utcnow().year}-{seq:04d}"

    @staticmethod
    def generate_sar(db: Session, case_id: int) -> SarReport | None:
        case = db.get(Case, case_id)
        if case is None:
            return None
        customer = db.get(Customer, case.customer_id)
        context = _build_context(db, case.customer_id)
        summary = case.ai_summary or generate_investigation_summary(context)
        if not case.ai_summary:
            case.ai_summary = summary
        sections = generate_sar_sections(context, summary)

        existing = db.query(SarReport).filter(SarReport.case_id == case_id).first()
        if existing is None:
            existing = SarReport(
                case_id=case_id,
                reference=AIService._reference(db, customer),
                summary="",
                customer_section="",
                reason="",
                recommendation="",
            )
            db.add(existing)

        existing.summary = sections["summary"]
        existing.customer_section = sections["customer_section"]
        existing.reason = sections["reason"]
        existing.evidence = sections["evidence"]
        existing.citations = sections["citations"]
        existing.timeline = sections["timeline"]
        existing.recommendation = sections["recommendation"]
        existing.analyst_notes = case.analyst_notes
        existing.generated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing)
        return existing
