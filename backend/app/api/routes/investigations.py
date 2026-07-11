from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import alerts as alerts_repo
from app.repositories import cases as cases_repo
from app.repositories import customers as customers_repo
from app.schemas.graph import GraphData
from app.schemas.investigation import InvestigationBundle
from app.schemas.timeline import TimelineEvent
from app.services.graph_service import build_customer_graph
from app.services.timeline_service import build_timeline

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.get("/{customer_id}", response_model=InvestigationBundle)
def get_investigation(customer_id: int, db: Session = Depends(get_db)):
    """Everything the investigation view needs, in one bundle."""
    customer = customers_repo.get_customer(db, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    graph = build_customer_graph(db, customer_id) or GraphData(nodes=[], edges=[])
    return InvestigationBundle(
        customer=customer,
        alerts=alerts_repo.for_customer(db, customer_id),
        cases=cases_repo.for_customer(db, customer_id),
        graph=graph,
        timeline=build_timeline(db, customer_id),
    )


@router.get("/{customer_id}/graph", response_model=GraphData)
def get_graph(customer_id: int, db: Session = Depends(get_db)):
    graph = build_customer_graph(db, customer_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return graph


@router.get("/{customer_id}/timeline", response_model=list[TimelineEvent])
def get_timeline(customer_id: int, db: Session = Depends(get_db)):
    return build_timeline(db, customer_id)
