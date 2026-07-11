"""Database engine, session factory, and declarative base.

The repositories layer is the only place that should import ``SessionLocal``
directly. Services receive a session via dependency injection.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

# SQLite needs check_same_thread disabled for use across FastAPI threads.
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=False,
    future=True,
)


if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fks(dbapi_connection, _connection_record):  # noqa: ANN001
        """Enforce foreign keys so ON DELETE CASCADE works on SQLite."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Create all tables. Imports models to register them on ``Base``."""
    from app import models  # noqa: F401  (ensures models are registered)

    Base.metadata.create_all(bind=engine)
    run_light_migrations()


_JSON_LIST_COLUMNS = {
    "citations",
    "evidence",
    "timeline",
    "triggered_rules",
    "breakdown",
}


def run_light_migrations() -> None:
    """Additively bring an existing SQLite DB up to the current model schema.

    ``create_all`` only creates missing *tables*, never missing *columns*, so a
    demo database seeded before a new column was introduced (e.g. the SAR
    ``citations`` column) keeps 500-ing on any query that touches that table.
    This adds any column present on a model but missing from the database, so
    the app self-heals without a reseed. SQLite-only; a no-op elsewhere.
    """
    if not _is_sqlite:
        return
    from sqlalchemy import inspect, text
    from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect

    from app import models  # noqa: F401  (ensure models are registered)

    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    dial = sqlite_dialect()

    with engine.begin() as conn:
        for table in Base.metadata.tables.values():
            if table.name not in existing_tables:
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                coltype = col.type.compile(dialect=dial)
                is_json_list = (
                    col.name in _JSON_LIST_COLUMNS or "JSON" in coltype.upper()
                )
                default = " DEFAULT '[]'" if is_json_list else ""
                conn.execute(
                    text(
                        f'ALTER TABLE "{table.name}" '
                        f'ADD COLUMN "{col.name}" {coltype}{default}'
                    )
                )
                if is_json_list:
                    conn.execute(
                        text(
                            f'UPDATE "{table.name}" SET "{col.name}" = \'[]\' '
                            f'WHERE "{col.name}" IS NULL'
                        )
                    )


def drop_all() -> None:
    """Drop all tables (used by the seeder for a clean slate)."""
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
