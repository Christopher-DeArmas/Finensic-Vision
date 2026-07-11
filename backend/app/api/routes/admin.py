"""Admin/utility endpoints for the demo (re-run scoring on demand)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import ScoringService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/rescore")
def rescore(db: Session = Depends(get_db)):
    """Re-run the AML engine over all customers; refresh scores + alerts."""
    return ScoringService(db).score_all()
