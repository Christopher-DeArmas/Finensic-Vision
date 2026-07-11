"""The rule engine: runs every rule for a customer and aggregates the score.

Scoring model: each fired rule contributes its point value; the raw sum is
capped/normalized to 0-100 and mapped to a risk band. Because every point is
attributable to a named rule with a reason, the resulting score is fully
explainable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.rules.base import RuleResult
from app.rules.context import RuleContext
from app.rules.rules import ALL_RULES
from app.utils.enums import RiskLevel, Severity

# Raw points are normalized against this reference so that reaching the
# critical band (76-100) requires several strong rules and 100 is very rare.
SCORE_MAX_REFERENCE = 130

_SEVERITY_ORDER = {
    Severity.LOW: 0,
    Severity.MEDIUM: 1,
    Severity.HIGH: 2,
    Severity.CRITICAL: 3,
}


@dataclass
class ScoreResult:
    """Aggregate output of the engine for one customer."""

    score: int
    risk_level: RiskLevel
    results: list[RuleResult] = field(default_factory=list)

    @property
    def triggered_rule_codes(self) -> list[str]:
        return [r.rule_code for r in self.results]

    @property
    def transaction_ids(self) -> list[int]:
        ids: list[int] = []
        for r in self.results:
            ids.extend(r.transaction_ids)
        return sorted(set(ids))

    @property
    def top_severity(self) -> Severity:
        if not self.results:
            return Severity.LOW
        return max((r.severity for r in self.results), key=lambda s: _SEVERITY_ORDER[s])

    def breakdown(self) -> list[dict]:
        return [r.as_dict() for r in self.results]


class RuleEngine:
    """Runs the configured rule set against a context."""

    def __init__(self, rules=None) -> None:
        self.rules = rules if rules is not None else ALL_RULES

    def evaluate(self, ctx: RuleContext) -> ScoreResult:
        results: list[RuleResult] = []
        for rule in self.rules:
            outcome = rule.evaluate(ctx)
            if outcome is not None:
                results.append(outcome)

        raw = sum(r.points for r in results)
        score = min(100, round(raw * 100 / SCORE_MAX_REFERENCE))
        return ScoreResult(
            score=score,
            risk_level=RiskLevel.from_score(score),
            results=results,
        )
