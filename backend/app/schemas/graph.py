from __future__ import annotations

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str  # "c<customer_id>" or "m<merchant_id>"
    kind: str  # "customer" | "merchant"
    label: str
    sublabel: str | None = None
    risk_level: str | None = None
    is_subject: bool = False
    is_high_risk: bool = False
    total_amount: float = 0.0


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    amount: float
    count: int
    suspicious: bool = False


class GraphData(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
