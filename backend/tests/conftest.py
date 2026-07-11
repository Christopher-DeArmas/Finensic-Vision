"""Pytest fixtures: a fresh, seeded in-memory-style database per test module."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.data import SyntheticDataGenerator


@pytest.fixture(scope="module")
def seeded_session(tmp_path_factory):
    """A temporary SQLite DB seeded with the deterministic synthetic dataset."""
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )

    @event.listens_for(engine, "connect")
    def _fk(dbapi_con, _rec):  # noqa: ANN001
        cur = dbapi_con.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)

    db = TestSession()
    SyntheticDataGenerator(db, seed=42).generate()
    db.commit()
    yield db
    db.close()
