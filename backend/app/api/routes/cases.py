from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import Pagination, pagination
from app.core.database import get_db
from app.models import Case
from app.repositories import cases as repo
from app.repositories import transactions as txn_repo
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.common import Page
from app.schemas.transaction import TransactionRead
from app.services import CaseService
from app.utils.enums import CaseStatus

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("", response_model=Page[CaseRead])
def list_cases(
    pg: Pagination = Depends(pagination),
    status: str | None = None,
    priority: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = repo.list_cases(
        db, page=pg.page, page_size=pg.page_size, status=status, priority=priority
    )
    return Page.build(items, total, pg.page, pg.page_size)


@router.post("", response_model=CaseRead, status_code=201)
def open_case(payload: CaseCreate, db: Session = Depends(get_db)):
    case = CaseService.create_from_alert(db, payload.alert_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return repo.get_case(db, case.id)


@router.get("/{case_id}", response_model=CaseRead)
def get_case(case_id: int, db: Session = Depends(get_db)):
    c = repo.get_case(db, case_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return c


@router.get("/{case_id}/transactions", response_model=list[TransactionRead])
def case_transactions(case_id: int, db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return txn_repo.enrich(db, list(c.transactions))


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(case_id: int, payload: CaseUpdate, db: Session = Depends(get_db)):
    c = db.get(Case, case_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Case not found")
    if payload.status is not None:
        c.status = payload.status
        if payload.status == CaseStatus.CLOSED.value and c.closed_at is None:
            c.closed_at = datetime.utcnow()
    if payload.priority is not None:
        c.priority = payload.priority
    if payload.analyst_notes is not None:
        c.analyst_notes = payload.analyst_notes
    db.commit()
    return repo.get_case(db, case_id)
