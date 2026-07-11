"""Prompt construction for AI investigation summaries and SARs."""

from __future__ import annotations

import json

SUMMARY_SYSTEM = (
    "You are a senior AML (anti-money-laundering) investigator at a major bank. "
    "You write concise, professional, regulator-ready analysis. You never "
    "fabricate facts beyond the structured evidence provided. Respond ONLY with "
    "valid JSON matching the requested schema."
)

SAR_SYSTEM = (
    "You are an AML compliance officer drafting a Suspicious Activity Report "
    "(SAR) narrative for filing. Write formal, factual, regulator-ready prose "
    "grounded strictly in the evidence provided. Every factual claim must be "
    "traceable to a numbered evidence citation ([R#] for a detection rule, [T#] "
    "for a transaction) supplied in the evidence catalog. Never assert a fact "
    "you cannot cite. Respond ONLY with valid JSON."
)


def summary_messages(context: dict) -> list[dict]:
    schema = {
        "executive_summary": "string (2-4 sentences)",
        "key_findings": ["string", "..."],
        "likely_behaviors": ["string", "..."],
        "risk_assessment": "string (2-3 sentences)",
        "recommended_next_steps": ["string", "..."],
    }
    user = (
        "Analyze the following AML case and produce an investigation summary.\n\n"
        f"CASE CONTEXT (JSON):\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"Return JSON with exactly these keys:\n{json.dumps(schema, indent=2)}"
    )
    return [
        {"role": "system", "content": SUMMARY_SYSTEM},
        {"role": "user", "content": user},
    ]


def sar_messages(context: dict, summary: dict, citations: list[dict]) -> list[dict]:
    schema = {
        "summary": "string (narrative overview, with inline [R#]/[T#] citations)",
        "reason": "string (why the activity is suspicious, with inline citations)",
        "recommendation": "string (recommended action, with inline citations)",
    }
    catalog = [
        {"id": c["id"], "kind": c["kind"], "evidence": c["label"], "detail": c["detail"]}
        for c in citations
    ]
    valid_ids = [c["id"] for c in citations]
    user = (
        "Draft the narrative sections of a SAR for the following case.\n\n"
        f"CASE CONTEXT (JSON):\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"PRIOR ANALYSIS (JSON):\n{json.dumps(summary, indent=2, default=str)}\n\n"
        "EVIDENCE CATALOG — cite these by id inline using square brackets, e.g. "
        "\"...structured cash deposits [R1] totalling $45,000 [T2]...\":\n"
        f"{json.dumps(catalog, indent=2, default=str)}\n\n"
        "CITATION RULES (mandatory):\n"
        f"- Only use ids from this exact list: {valid_ids}.\n"
        "- Every material factual claim MUST end with at least one [id] citation.\n"
        "- Do NOT invent ids, facts, figures, or evidence not in the catalog.\n"
        "- Each of the three sections must contain at least one valid citation.\n\n"
        f"Return JSON with exactly these keys:\n{json.dumps(schema, indent=2)}"
    )
    return [
        {"role": "system", "content": SAR_SYSTEM},
        {"role": "user", "content": user},
    ]
