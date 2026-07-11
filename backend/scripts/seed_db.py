"""Seed the Sentinel AML database with synthetic data.

Usage:
    python -m scripts.seed_db            # uses SEED from .env (default 42)
    python -m scripts.seed_db --seed 7   # override seed
    python -m scripts.seed_db --keep     # do not drop existing tables first

Run from the ``backend/`` directory.
"""

from __future__ import annotations

import argparse

from app.core.config import settings
from app.core.database import SessionLocal, create_all, drop_all
from app.data import SyntheticDataGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the Sentinel AML database.")
    parser.add_argument(
        "--seed",
        type=int,
        default=settings.seed,
        help="RNG seed for reproducible data (default from .env).",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep existing tables instead of dropping them first.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Sentinel AML - database seeder")
    print("=" * 60)
    print(f"  Database : {settings.database_url}")
    print(f"  Seed     : {args.seed}")
    print("-" * 60)

    if not args.keep:
        print("  Dropping existing tables...")
        drop_all()
    print("  Creating tables...")
    create_all()

    db = SessionLocal()
    try:
        print("  Generating synthetic data (this takes a few seconds)...")
        generator = SyntheticDataGenerator(db, seed=args.seed)
        summary = generator.generate()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("-" * 60)
    print("  Seed complete. Row counts:")
    print(f"    customers     : {summary.customers}")
    print(f"    accounts      : {summary.accounts}")
    print(f"    merchants     : {summary.merchants}")
    print(f"    transactions  : {summary.transactions}")
    print(f"    relationships : {summary.relationships}")
    print("-" * 60)
    print("  Planted laundering scenarios:")
    for tag, desc in summary.scenarios.items():
        print(f"    [{tag}]")
        print(f"        {desc}")
    print("=" * 60)


if __name__ == "__main__":
    main()
