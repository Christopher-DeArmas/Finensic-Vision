"""Reset the demo database: seed synthetic data, then run the AML engine.

One command to get a fully populated, scored database ready for the API:

    python -m scripts.reset_demo

Equivalent to running ``scripts.seed_db`` followed by ``scripts.run_scoring``.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.database import SessionLocal, create_all, drop_all
from app.data import SyntheticDataGenerator
from app.services import ScoringService


def main() -> None:
    print("=" * 60)
    print("  Finensic Vision - demo reset (seed + score)")
    print("=" * 60)
    print(f"  Database : {settings.database_url}")

    drop_all()
    create_all()

    db = SessionLocal()
    try:
        gen = SyntheticDataGenerator(db, seed=settings.seed)
        summary = gen.generate()
        db.commit()
        print(
            f"  Seeded   : {summary.customers} customers, "
            f"{summary.transactions} transactions"
        )

        result = ScoringService(db).score_all()
        print(
            f"  Scored   : {result['distribution']} | "
            f"{result['alerts_created']} alerts"
        )
    finally:
        db.close()

    print("-" * 60)
    print("  Ready. Start the API with:")
    print("      uvicorn app.main:app --reload")
    print("  Then open http://localhost:8000/docs")
    print("=" * 60)


if __name__ == "__main__":
    main()
