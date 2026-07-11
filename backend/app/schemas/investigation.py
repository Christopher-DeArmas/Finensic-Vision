from __future__ import annotations

from pydantic import BaseModel

from app.schemas.alert import AlertRead
from app.schemas.case import CaseRead
from app.schemas.customer import CustomerDetail
from app.schemas.graph import GraphData
from app.schemas.timeline import TimelineEvent


class InvestigationBundle(BaseModel):
    customer: CustomerDetail
    alerts: list[AlertRead]
    cases: list[CaseRead]
    graph: GraphData
    timeline: list[TimelineEvent]
