from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import RiskScore
from app.schemas.risk_score import RiskScoreRead

router = APIRouter(prefix="/risk-scores", tags=["risk-scores"])


@router.get("/customer/{customer_id}", response_model=list[RiskScoreRead])
def customer_risk_history(customer_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(RiskScore)
        .filter(RiskScore.customer_id == customer_id)
        .order_by(RiskScore.id.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No risk scores for customer")
    return rows
