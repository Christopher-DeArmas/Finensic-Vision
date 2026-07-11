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
    "grounded strictly in the evidence provided. Respond ONLY with valid JSON."
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


def sar_messages(context: dict, summary: dict) -> list[dict]:
    schema = {
        "summary": "string (narrative overview)",
        "reason": "string (why the activity is suspicious)",
        "recommendation": "string (recommended action)",
    }
    user = (
        "Draft the narrative sections of a SAR for the following case.\n\n"
        f"CASE CONTEXT (JSON):\n{json.dumps(context, indent=2, default=str)}\n\n"
        f"PRIOR ANALYSIS (JSON):\n{json.dumps(summary, indent=2, default=str)}\n\n"
        f"Return JSON with exactly these keys:\n{json.dumps(schema, indent=2)}"
    )
    return [
        {"role": "system", "content": SAR_SYSTEM},
        {"role": "user", "content": user},
    ]
