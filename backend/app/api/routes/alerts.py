from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import Pagination, pagination
from app.core.database import get_db
from app.models import Alert
from app.repositories import alerts as repo
from app.repositories import transactions as txn_repo
from app.schemas.alert import AlertRead, AlertUpdate
from app.schemas.common import Page
from app.schemas.transaction import TransactionRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=Page[AlertRead])
def list_alerts(
    pg: Pagination = Depends(pagination),
    severity: str | None = None,
    status: str | None = None,
    rule: str | None = None,
    sort: str = "triage",
    db: Session = Depends(get_db),
):
    items, total = repo.list_alerts(
        db,
        page=pg.page,
        page_size=pg.page_size,
        severity=severity,
        status=status,
        rule=rule,
        sort=sort,
    )
    return Page.build(items, total, pg.page, pg.page_size)


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    a = repo.get_alert(db, alert_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return a


@router.get("/{alert_id}/transactions", response_model=list[TransactionRead])
def alert_transactions(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return txn_repo.enrich(db, list(a.transactions))


@router.patch("/{alert_id}", response_model=AlertRead)
def update_alert(alert_id: int, payload: AlertUpdate, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    a.status = payload.status
    db.commit()
    return repo.get_alert(db, alert_id)
