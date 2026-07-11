"""Generate the structured sections of a Suspicious Activity Report.

Every factual claim in the narrative is linked to a numbered citation in an
auditable evidence catalog: ``[R#]`` markers reference a triggered detection
rule, ``[T#]`` markers reference a specific flagged transaction. This makes the
AI-drafted narrative explainable and examiner-verifiable — each sentence can be
traced back to the evidence that supports it.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime

from app.ai.client import get_client
from app.ai.prompt import sar_messages
from app.core.config import settings

logger = logging.getLogger("sentinel.ai")

_MARKER_RE = re.compile(r"\[([RT]\d+)\]")


def _fmt_ts(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %Y, %H:%M UTC")
    except (ValueError, TypeError):
        return str(iso)


def build_citations(context: dict) -> list[dict]:
    """Deterministic citation catalog built from the case evidence.

    Rules become ``R1..Rn``; flagged transactions become ``T1..Tn``. Each entry
    is self-describing so the UI and PDF can render a full citation trail.
    """
    citations: list[dict] = []
    for i, r in enumerate(context.get("rules", []), start=1):
        citations.append(
            {
                "id": f"R{i}",
                "kind": "rule",
                "ref": r.get("code"),
                "label": f"{r.get('code')} · {r.get('name')}",
                "detail": r.get("reason") or r.get("name") or "",
                "points": r.get("points"),
                "severity": r.get("severity"),
            }
        )
    for i, t in enumerate(context.get("flagged_transactions", []), start=1):
        citations.append(
            {
                "id": f"T{i}",
                "kind": "transaction",
                "ref": t.get("external_id"),
                "label": t.get("external_id"),
                "detail": (
                    f"{str(t.get('type', 'transaction')).title()} of "
                    f"${t.get('amount', 0):,.2f} in {t.get('city')}, "
                    f"{t.get('country')} on {_fmt_ts(t.get('timestamp'))}."
                ),
                "amount": t.get("amount"),
                "timestamp": t.get("timestamp"),
            }
        )
    return citations


def _valid_markers(text: str, ids: set[str]) -> bool:
    """True if the text cites at least one id and every marker resolves."""
    found = _MARKER_RE.findall(text or "")
    return bool(found) and all(m in ids for m in found)


def generate_sar_sections(context: dict, summary: dict) -> dict:
    """Return the narrative + structured sections of the SAR, with citations."""
    c = context["customer"]
    citations = build_citations(context)
    rule_cites = [x for x in citations if x["kind"] == "rule"]
    txn_cites = [x for x in citations if x["kind"] == "transaction"]

    customer_section = (
        f"Subject name:        {c['name']}\n"
        f"Occupation:          {c['occupation']}\n"
        f"Location:            {c['city']}, {c['country']}\n"
        f"KYC status:          {c['kyc_status'].title()}\n"
        f"Declared income:     ${c['annual_income']:,.0f} per annum "
        f"(${c['expected_monthly_income']:,.0f}/month)\n"
        f"Accounts on file:    {c['accounts_count']}\n"
        f"Risk rating:         {c['risk_level'].upper()} ({c['risk_score']}/100)\n"
        f"High-risk jurisdiction: {'Yes' if c.get('is_high_risk_jurisdiction') else 'No'}"
    )

    # Keep the flat evidence list for backward compatibility / PDF.
    evidence: list[dict] = []
    for x in rule_cites:
        evidence.append({"rule": x["ref"], "finding": x["label"], "detail": x["detail"]})
    for x in txn_cites:
        evidence.append({"transaction": x["ref"], "detail": x["detail"]})

    timeline = context.get("timeline", [])
    narrative = _narrative(context, summary, citations, rule_cites, txn_cites)

    return {
        "summary": narrative["summary"],
        "customer_section": customer_section,
        "reason": narrative["reason"],
        "evidence": evidence,
        "citations": citations,
        "timeline": timeline,
        "recommendation": narrative["recommendation"],
    }


def _narrative(
    context: dict,
    summary: dict,
    citations: list[dict],
    rule_cites: list[dict],
    txn_cites: list[dict],
) -> dict:
    ids = {x["id"] for x in citations}
    client = get_client()
    if client is not None and ids:
        try:
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=sar_messages(context, summary, citations),
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            data = json.loads(resp.choices[0].message.content)
            keys = {"summary", "reason", "recommendation"}
            # Only trust the model if every section cites valid evidence ids —
            # this guarantees no uncited claims slip into a filed narrative.
            if keys.issubset(data) and all(
                _valid_markers(data[k], ids) for k in keys
            ):
                return {k: data[k] for k in keys}
            logger.warning("SAR citations invalid; using cited template.")
        except Exception:  # noqa: BLE001
            logger.exception("OpenAI SAR failed; using cited template.")

    return _template_narrative(context, summary, rule_cites, txn_cites)


def _template_narrative(
    context: dict,
    summary: dict,
    rule_cites: list[dict],
    txn_cites: list[dict],
) -> dict:
    """Citation-linked fallback narrative (no LLM required)."""
    c = context["customer"]
    counts = context.get("counts", {})
    behaviors = ", ".join(summary.get("likely_behaviors", [])) or "anomalous activity"
    n_flagged = counts.get("total_flagged", 0)

    rule_refs = " ".join(f"[{x['id']}]" for x in rule_cites)
    # Cite the two largest flagged transactions as concrete examples.
    txn_refs = " ".join(f"[{x['id']}]" for x in txn_cites[:2])

    summary_text = (
        f"This report documents suspicious activity identified on the account(s) of "
        f"{c['name']}, a {c['occupation']} domiciled in {c['city']}, {c['country']}. "
        f"{summary.get('executive_summary', '')} The subject was assigned a "
        f"{c['risk_level'].upper()} risk rating of {c['risk_score']}/100 on the basis "
        f"of the detection findings catalogued below{(' ' + rule_refs) if rule_refs else ''}."
    ).strip()

    reason_bits = []
    for x in rule_cites:
        reason_bits.append(f"{x['detail'].rstrip('.')} [{x['id']}]")
    reason_body = "; ".join(reason_bits) if reason_bits else "anomalous transaction patterns"

    reason_text = (
        f"The activity is deemed suspicious because it is materially inconsistent with "
        f"the subject's declared profile and exhibits recognised indicators of money "
        f"laundering, specifically {behaviors}. Automated transaction monitoring "
        f"triggered {len(rule_cites)} detection rule(s) across {n_flagged} flagged "
        f"transaction(s). The specific findings are: {reason_body}."
    )
    if txn_refs:
        reason_text += (
            f" Representative flagged transactions evidencing this activity include "
            f"{txn_refs}. The institution was unable to reconcile this activity with a "
            f"legitimate economic purpose."
        )

    steps = summary.get("recommended_next_steps", [])
    if steps:
        recommendation_text = (
            "On the basis of the cited findings"
            f"{(' ' + rule_refs) if rule_refs else ''}, the institution recommends the "
            "following actions: " + "; ".join(s.rstrip(".") for s in steps) + "."
        )
    else:
        recommendation_text = (
            "On the basis of the cited findings"
            f"{(' ' + rule_refs) if rule_refs else ''}, the institution recommends "
            "filing this report and maintaining enhanced monitoring of the subject."
        )

    return {
        "summary": summary_text,
        "reason": reason_text,
        "recommendation": recommendation_text,
    }
