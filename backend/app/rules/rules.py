"""The ten explainable AML heuristic rules.

Each rule is a pure function of the ``RuleContext``. Point values follow the
project's risk-scoring scheme; every fired rule attaches a human-readable
reason and the transaction ids that constitute its evidence.
"""

from __future__ import annotations

from datetime import timedelta

from app.rules.base import Rule, RuleResult
from app.rules.context import RuleContext, TxnView
from app.utils.enums import PaymentMethod, Severity, TransactionType
from app.utils.geo import implied_speed_kmh

# --- shared thresholds -----------------------------------------------------
STRUCTURING_LOW = 9_000.0
STRUCTURING_HIGH = 10_000.0
STRUCTURING_MIN_COUNT = 3
STRUCTURING_WINDOW = timedelta(days=30)

LARGE_AMOUNT = 10_000.0
RAPID_LARGE_INBOUND = 25_000.0  # above normal salary/deposit range
RAPID_WINDOW = timedelta(hours=2)
RAPID_DISPERSION_RATIO = 0.4

DORMANT_GAP = timedelta(days=180)
DORMANT_LARGE_INBOUND = 50_000.0

VELOCITY_WINDOW = timedelta(minutes=60)
VELOCITY_MIN_COUNT = 8

GEO_IMPOSSIBLE_KMH = 1_200.0  # above the fastest commercial aircraft

MULTI_SOURCE_WINDOW = timedelta(days=7)
MULTI_SOURCE_MIN = 15

CASH_LARGE = 10_000.0
CASH_DAILY_AGG = 15_000.0

NEW_ACCOUNT_AGE = timedelta(days=30)
EXPLOSION_VOLUME = 100_000.0

HIGH_RISK_MERCHANT_CATS = {"crypto_exchange", "casino", "money_transfer"}


def _max_in_window(timestamps: list, window: timedelta) -> int:
    """Max number of items falling within any sliding ``window`` (sorted asc)."""
    ts = sorted(timestamps)
    best = 0
    start = 0
    for end in range(len(ts)):
        while ts[end] - ts[start] > window:
            start += 1
        best = max(best, end - start + 1)
    return best


# --------------------------------------------------------------------------
# Rule 1 — Structuring
# --------------------------------------------------------------------------
class StructuringRule(Rule):
    code = "AML-01"
    name = "Structuring"
    points = 30
    severity = Severity.HIGH

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        hits = [
            t
            for t in ctx.inbound
            if t.transaction_type == TransactionType.DEPOSIT.value
            and STRUCTURING_LOW <= t.amount < STRUCTURING_HIGH
        ]
        if len(hits) < STRUCTURING_MIN_COUNT:
            return None
        window_max = _max_in_window([t.timestamp for t in hits], STRUCTURING_WINDOW)
        if window_max < STRUCTURING_MIN_COUNT:
            return None
        total = sum(t.amount for t in hits)
        reason = (
            f"{len(hits)} deposits between ${STRUCTURING_LOW:,.0f} and "
            f"${STRUCTURING_HIGH:,.0f} (just below the $10,000 reporting "
            f"threshold), {window_max} within a 30-day window, totaling "
            f"${total:,.0f} — a classic structuring/smurfing pattern."
        )
        return self._result(reason, [t.id for t in hits])


# --------------------------------------------------------------------------
# Rule 2 — Rapid Movement of Funds
# --------------------------------------------------------------------------
class RapidMovementRule(Rule):
    code = "AML-02"
    name = "Rapid Movement"
    points = 40
    severity = Severity.HIGH

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        evidence: list[int] = []
        pairs = 0
        for inb in ctx.inbound:
            if inb.amount < RAPID_LARGE_INBOUND:
                continue
            # Aggregate *all* outflows within the window — layering typically
            # splits a large inbound into several smaller onward payments
            # (e.g. multiple crypto purchases) rather than one equal transfer.
            window_out = [
                out
                for out in ctx.outbound
                if inb.timestamp <= out.timestamp <= inb.timestamp + RAPID_WINDOW
            ]
            dispersed = sum(o.amount for o in window_out)
            if dispersed >= RAPID_DISPERSION_RATIO * inb.amount:
                pairs += 1
                evidence.append(inb.id)
                evidence.extend(o.id for o in window_out)
        if pairs == 0:
            return None
        reason = (
            f"{pairs} instance(s) of large inbound funds (>= "
            f"${RAPID_LARGE_INBOUND:,.0f}) largely dispersed within 2 hours of "
            f"arriving — pass-through / layering behavior."
        )
        return self._result(reason, evidence)


# --------------------------------------------------------------------------
# Rule 3 — Circular Transfers
# --------------------------------------------------------------------------
class CircularTransferRule(Rule):
    code = "AML-03"
    name = "Circular Transfers"
    points = 60
    severity = Severity.CRITICAL

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        if not ctx.cycles:
            return None
        ring = ctx.cycles[0]
        reason = (
            f"Customer participates in a circular transfer ring of "
            f"{len(ring)} accounts (A -> B -> C -> A). Funds return to the "
            f"originator, a strong indicator of layering."
        )
        return self._result(reason, ctx.cycle_transaction_ids)


# --------------------------------------------------------------------------
# Rule 4 — Dormant Account Awakening
# --------------------------------------------------------------------------
class DormantAccountRule(Rule):
    code = "AML-04"
    name = "Dormant Account Awakening"
    points = 40
    severity = Severity.HIGH

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        evidence: list[int] = []
        for acc in ctx.accounts:
            acc_txns = sorted(
                [t for t in ctx.all_txns if t.account_id == acc.id],
                key=lambda t: t.timestamp,
            )
            prev_ts = acc.opened_at
            for t in acc_txns:
                gap = t.timestamp - prev_ts
                if (
                    t.direction == "in"
                    and t.amount >= DORMANT_LARGE_INBOUND
                    and gap >= DORMANT_GAP
                ):
                    evidence.append(t.id)
                prev_ts = t.timestamp
        if not evidence:
            return None
        reason = (
            "A large deposit landed on an account that had been inactive for "
            "6+ months — dormant-account reactivation often signals a mule or "
            "compromised account."
        )
        return self._result(reason, evidence)


# --------------------------------------------------------------------------
# Rule 5 — Velocity
# --------------------------------------------------------------------------
class VelocityRule(Rule):
    code = "AML-05"
    name = "Velocity"
    points = 25
    severity = Severity.MEDIUM

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        transfers = [
            t
            for t in ctx.outbound
            if t.transaction_type == TransactionType.TRANSFER.value
        ]
        if len(transfers) < VELOCITY_MIN_COUNT:
            return None
        burst = _max_in_window([t.timestamp for t in transfers], VELOCITY_WINDOW)
        if burst < VELOCITY_MIN_COUNT:
            return None
        reason = (
            f"{burst} outgoing transfers within a single 60-minute window — "
            f"abnormally high velocity consistent with rapid fund dispersion."
        )
        return self._result(reason, [t.id for t in transfers])


# --------------------------------------------------------------------------
# Rule 6 — Geographic Anomaly
# --------------------------------------------------------------------------
class GeographicAnomalyRule(Rule):
    code = "AML-06"
    name = "Geographic Anomaly"
    points = 20
    severity = Severity.MEDIUM

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        txns = ctx.located_txns
        evidence: list[int] = []
        detail = ""
        for a, b in zip(txns, txns[1:]):
            hours = (b.timestamp - a.timestamp).total_seconds() / 3600.0
            speed = implied_speed_kmh(
                a.latitude, a.longitude, b.latitude, b.longitude, hours
            )
            if speed > GEO_IMPOSSIBLE_KMH and a.city != b.city:
                evidence.extend([a.id, b.id])
                if not detail:
                    detail = f"{a.city} then {b.city} ~{max(hours, 0.0) * 60:.0f} min apart"
        if not evidence:
            return None
        reason = (
            f"Transactions in physically impossible succession ({detail}) — "
            f"implied travel speed exceeds any aircraft, indicating card/account "
            f"compromise or coordinated use."
        )
        return self._result(reason, evidence)


# --------------------------------------------------------------------------
# Rule 7 — Multiple Incoming Sources
# --------------------------------------------------------------------------
class MultipleIncomingSourcesRule(Rule):
    code = "AML-07"
    name = "Multiple Incoming Sources"
    points = 45
    severity = Severity.HIGH

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        transfers = [
            t
            for t in ctx.inbound
            if t.transaction_type == TransactionType.TRANSFER.value
            and t.counterparty_customer_id is not None
        ]
        if not transfers:
            return None
        transfers.sort(key=lambda t: t.timestamp)
        # Slide a 7-day window and count distinct senders inside it.
        best_sources: set[int] = set()
        start = 0
        for end in range(len(transfers)):
            while transfers[end].timestamp - transfers[start].timestamp > MULTI_SOURCE_WINDOW:
                start += 1
            window_sources = {
                transfers[i].counterparty_customer_id for i in range(start, end + 1)
            }
            if len(window_sources) > len(best_sources):
                best_sources = window_sources
        if len(best_sources) < MULTI_SOURCE_MIN:
            return None
        evidence = [
            t.id for t in transfers if t.counterparty_customer_id in best_sources
        ]
        reason = (
            f"{len(best_sources)} unrelated accounts funneled money into this "
            f"account within 7 days — a hallmark of a money-mule collection "
            f"account."
        )
        return self._result(reason, evidence)


# --------------------------------------------------------------------------
# Rule 8 — High-Risk Jurisdiction
# --------------------------------------------------------------------------
class HighRiskJurisdictionRule(Rule):
    code = "AML-08"
    name = "High-Risk Jurisdiction"
    points = 15
    severity = Severity.MEDIUM

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        hr_txns = [
            t for t in ctx.all_txns if t.country in ctx.high_risk_countries
        ]
        if not hr_txns and not ctx.customer.is_high_risk_jurisdiction:
            return None
        countries = sorted({t.country for t in hr_txns}) or [ctx.customer.country]
        reason = (
            f"Activity linked to high-risk jurisdiction(s): "
            f"{', '.join(countries)}."
        )
        return self._result(reason, [t.id for t in hr_txns])


# --------------------------------------------------------------------------
# Rule 9 — Large Cash Deposit
# --------------------------------------------------------------------------
class LargeCashDepositRule(Rule):
    code = "AML-09"
    name = "Large Cash Deposit"
    points = 20
    severity = Severity.MEDIUM

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        cash = [
            t
            for t in ctx.inbound
            if t.payment_method == PaymentMethod.CASH.value
            and t.transaction_type == TransactionType.DEPOSIT.value
        ]
        singles = [t for t in cash if t.amount >= CASH_LARGE]
        # Daily aggregation for sub-threshold-but-large same-day cash.
        by_day: dict = {}
        for t in cash:
            by_day.setdefault(t.timestamp.date(), []).append(t)
        agg_days = [
            day for day, items in by_day.items()
            if sum(i.amount for i in items) >= CASH_DAILY_AGG
        ]
        if not singles and not agg_days:
            return None
        evidence = [t.id for t in singles] or [
            t.id for day in agg_days for t in by_day[day]
        ]
        reason = (
            "Large cash deposit activity detected (individual deposits over "
            "$10,000 or $15,000+ aggregated in a single day)."
        )
        return self._result(reason, evidence)


# --------------------------------------------------------------------------
# Rule 10 — Account Explosion
# --------------------------------------------------------------------------
class AccountExplosionRule(Rule):
    code = "AML-10"
    name = "Account Explosion"
    points = 40
    severity = Severity.HIGH

    def evaluate(self, ctx: RuleContext) -> RuleResult | None:
        account_age = ctx.now - ctx.customer.date_opened
        if account_age > NEW_ACCOUNT_AGE:
            return None
        early_inbound = [
            t
            for t in ctx.inbound
            if t.timestamp <= ctx.customer.date_opened + NEW_ACCOUNT_AGE
        ]
        volume = sum(t.amount for t in early_inbound)
        if volume < EXPLOSION_VOLUME:
            return None
        reason = (
            f"A {account_age.days}-day-old account received ${volume:,.0f} "
            f"across {len(early_inbound)} inbound transfers shortly after "
            f"opening — anomalous volume for a brand-new account."
        )
        return self._result(reason, [t.id for t in early_inbound])


# The ordered rule set the engine runs.
ALL_RULES: list[Rule] = [
    StructuringRule(),
    RapidMovementRule(),
    CircularTransferRule(),
    DormantAccountRule(),
    VelocityRule(),
    GeographicAnomalyRule(),
    MultipleIncomingSourcesRule(),
    HighRiskJurisdictionRule(),
    LargeCashDepositRule(),
    AccountExplosionRule(),
]
