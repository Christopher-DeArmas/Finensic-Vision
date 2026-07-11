"""Base types for the AML rule engine.

Rules are *pure*: they take a ``RuleContext`` (plain data) and return a
``RuleResult`` or ``None``. They never touch the database. This keeps every
risk point fully explainable and makes rules trivial to unit-test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.utils.enums import Severity


@dataclass
class RuleResult:
    """The outcome of a single rule that fired for a customer."""

    rule_code: str
    rule_name: str
    points: int
    reason: str
    severity: Severity
    transaction_ids: list[int] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "rule": self.rule_code,
            "name": self.rule_name,
            "points": self.points,
            "reason": self.reason,
            "severity": self.severity.value,
            "transaction_ids": self.transaction_ids,
        }


class Rule:
    """Base class for all AML heuristic rules.

    Subclasses set ``code``/``name``/``points``/``severity`` and implement
    :meth:`evaluate`, returning a ``RuleResult`` when the rule fires or ``None``
    otherwise.
    """

    code: str = ""
    name: str = ""
    points: int = 0
    severity: Severity = Severity.LOW

    def evaluate(self, ctx: "RuleContext") -> RuleResult | None:  # noqa: F821
        raise NotImplementedError

    # Convenience for subclasses to build a result with the class metadata.
    def _result(
        self, reason: str, transaction_ids: list[int] | None = None
    ) -> RuleResult:
        return RuleResult(
            rule_code=self.code,
            rule_name=self.name,
            points=self.points,
            reason=reason,
            severity=self.severity,
            transaction_ids=transaction_ids or [],
        )
