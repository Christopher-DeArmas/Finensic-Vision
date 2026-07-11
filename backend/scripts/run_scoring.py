"""Run the AML rule engine over every customer in the database.

Usage (from backend/):
    python -m scripts.run_scoring

Scores all customers, persists risk_scores + alerts, and prints a summary
including the planted scenario customers so you can verify detection.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Customer, RiskScore
from app.services import ScoringService


def main() -> None:
    print("=" * 64)
    print("  Sentinel AML - rule engine")
    print("=" * 64)
    print(f"  Database        : {settings.database_url}")
    print(f"  Alert threshold : {settings.alert_threshold}")
    print("-" * 64)

    db = SessionLocal()
    try:
        summary = ScoringService(db).score_all()

        print("  Risk distribution:")
        for level in ("critical", "high", "medium", "low"):
            print(f"    {level:<9}: {summary['distribution'][level]}")
        print(f"  Alerts created  : {summary['alerts_created']}")
        print("-" * 64)
        print("  Top risk customers:")
        for row in summary["top_risk"]:
            rules = ", ".join(row["rules"])
            print(f"    {row['score']:>3} [{row['level']:<8}] {row['customer']:<26} {rules}")

        print("-" * 64)
        print("  Planted scenario detection:")
        scenario_customers = (
            db.query(Customer)
            .filter(Customer.scenario_tag.isnot(None))
            .order_by(Customer.scenario_tag)
            .all()
        )
        for c in scenario_customers:
            rs = (
                db.query(RiskScore)
                .filter(RiskScore.customer_id == c.id)
                .order_by(RiskScore.id.desc())
                .first()
            )
            codes = ", ".join(r["rule"] for r in rs.breakdown) if rs else "-"
            score = rs.score if rs else 0
            level = rs.risk_level if rs else "-"
            print(f"    {c.scenario_tag:<18} {score:>3} [{level:<8}] {c.full_name:<24} -> {codes}")
        print("=" * 64)
    finally:
        db.close()


if __name__ == "__main__":
    main()
