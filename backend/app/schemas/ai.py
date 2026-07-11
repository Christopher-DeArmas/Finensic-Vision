from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AISummary(BaseModel):
    executive_summary: str
    key_findings: list[str]
    likely_behaviors: list[str]
    risk_assessment: str
    recommended_next_steps: list[str]
    generated_by: str = "template"
    model: str | None = None


class SarReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    reference: str
    summary: str
    customer_section: str
    reason: str
    evidence: list
    citations: list = []
    timeline: list
    recommendation: str
    analyst_notes: str | None
    generated_at: datetime
