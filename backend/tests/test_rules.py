"""Verify rule detection and the shape of the risk population."""

from collections import Counter

import pytest

from app.models import Alert, Customer, RiskScore
from app.services import ScoringService

# scenario_tag -> a rule code that must appear for that planted customer
EXPECTED_RULE = {
    "structuring": "AML-01",
    "rapid_movement": "AML-02",
    "circular_ring": "AML-03",
    "dormant_awakening": "AML-04",
    "velocity_burst": "AML-05",
    "geo_anomaly": "AML-06",
    "money_mule": "AML-07",
    "crypto_layering": "AML-02",
    "account_explosion": "AML-10",
}


@pytest.fixture(scope="module")
def scored(seeded_session):
    ScoringService(seeded_session).score_all()
    return seeded_session


def _latest_score(db, customer_id):
    return (
        db.query(RiskScore)
        .filter(RiskScore.customer_id == customer_id)
        .order_by(RiskScore.id.desc())
        .first()
    )


@pytest.mark.parametrize("tag,rule_code", EXPECTED_RULE.items())
def test_scenario_triggers_expected_rule(scored, tag, rule_code):
    customers = scored.query(Customer).filter(Customer.scenario_tag == tag).all()
    assert customers, f"no customer for scenario {tag}"
    fired = any(
        rule_code in {b["rule"] for b in (_latest_score(scored, c.id).breakdown or [])}
        for c in customers
    )
    assert fired, f"scenario {tag} did not trigger {rule_code}"


def test_all_rules_fire_somewhere(scored):
    codes: set[str] = set()
    for rs in scored.query(RiskScore).all():
        codes.update(b["rule"] for b in rs.breakdown)
    expected = {f"AML-{i:02d}" for i in range(1, 11)}
    assert expected.issubset(codes), f"rules never fired: {expected - codes}"


def test_alerts_created_for_high_risk(scored):
    alerts = scored.query(Alert).all()
    assert len(alerts) >= 6
    assert all(a.triggered_rules for a in alerts)


def test_risk_distribution_shape(scored):
    customers = scored.query(Customer).all()
    n = len(customers)
    counts = Counter(c.risk_level for c in customers)
    # Low is the largest band; medium/high present; critical a small minority.
    assert counts["low"] == max(counts.values())
    assert counts["medium"] > 0 and counts["high"] > 0
    assert counts["critical"] / n < 0.18


def test_no_transaction_predates_account(scored):
    from sqlalchemy import or_
    from app.models import Account, Transaction

    bad = 0
    for a in scored.query(Account).all():
        bad += (
            scored.query(Transaction)
            .filter(
                or_(
                    Transaction.sender_account_id == a.id,
                    Transaction.receiver_account_id == a.id,
                ),
                Transaction.timestamp < a.opened_at,
            )
            .count()
        )
    assert bad == 0
