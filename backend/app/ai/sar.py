"""Generate the structured sections of a Suspicious Activity Report."""

from __future__ import annotations

import json
import logging

from app.ai.client import get_client
from app.ai.prompt import sar_messages
from app.core.config import settings

logger = logging.getLogger("sentinel.ai")


def generate_sar_sections(context: dict, summary: dict) -> dict:
    """Return {summary, customer_section, reason, evidence, timeline, recommendation}."""
    c = context["customer"]

    # Structured (deterministic) sections built from the evidence.
    customer_section = (
        f"Subject: {c['name']}\n"
        f"Occupation: {c['occupation']}\n"
        f"Location: {c['city']}, {c['country']}\n"
        f"KYC status: {c['kyc_status']}\n"
        f"Declared annual income: ${c['annual_income']:,.0f}\n"
        f"Risk rating: {c['risk_level'].upper()} ({c['risk_score']}/100)\n"
        f"High-risk jurisdiction: {'Yes' if c.get('is_high_risk_jurisdiction') else 'No'}"
    )
    evidence = [
        {
            "rule": r["code"],
            "finding": r["name"],
            "points": r["points"],
            "detail": r["reason"],
        }
        for r in context.get("rules", [])
    ]
    for t in context.get("flagged_transactions", [])[:10]:
        evidence.append(
            {
                "transaction": t["external_id"],
                "detail": f"{t['type']} of ${t['amount']:,.0f} in {t['city']}, "
                f"{t['country']} on {t['timestamp']}",
            }
        )
    timeline = context.get("timeline", [])

    # Narrative sections — AI if available, else templated.
    narrative = _narrative(context, summary)

    return {
        "summary": narrative["summary"],
        "customer_section": customer_section,
        "reason": narrative["reason"],
        "evidence": evidence,
        "timeline": timeline,
        "recommendation": narrative["recommendation"],
    }


def _narrative(context: dict, summary: dict) -> dict:
    client = get_client()
    if client is not None:
        try:
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=sar_messages(context, summary),
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            data = json.loads(resp.choices[0].message.content)
            if {"summary", "reason", "recommendation"}.issubset(data):
                return data
        except Exception:  # noqa: BLE001
            logger.exception("OpenAI SAR failed; using template.")

    c = context["customer"]
    behaviors = ", ".join(summary.get("likely_behaviors", [])) or "anomalous activity"
    return {
        "summary": summary.get("executive_summary")
        or f"This report concerns suspicious activity by {c['name']}.",
        "reason": (
            f"The activity is considered suspicious due to {behaviors}. "
            f"{len(context.get('rules', []))} AML detection rule(s) were triggered, "
            f"yielding a risk rating of {c['risk_level'].upper()} "
            f"({c['risk_score']}/100)."
        ),
        "recommendation": " ".join(summary.get("recommended_next_steps", []))
        or "File this SAR and continue enhanced monitoring.",
    }
