"""Verify every planted laundering scenario is detected by the right rule."""

import pytest

from app.models import Alert, Customer, RiskScore
from app.services import ScoringService

# scenario_tag -> rule code that must appear in the customer's breakdown
EXPECTED_RULE = {
    "structuring": "AML-01",
    "rapid_movement": "AML-02",
    "circular_ring": "AML-03",
    "dormant_awakening": "AML-04",
    "velocity_burst": "AML-05",
    "geo_anomaly": "AML-06",
    "money_mule": "AML-07",
    "crypto_layering": "AML-02",  # large inbound rapidly layered out via crypto
    "account_explosion": "AML-10",
}

# Scenarios the brief requires to open an investigation (>= alert threshold).
MUST_ALERT = {
    "structuring",
    "circular_ring",
    "money_mule",
    "crypto_layering",
    "account_explosion",
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
    # At least one customer with this tag must fire the expected rule.
    fired = False
    for c in customers:
        rs = _latest_score(scored, c.id)
        assert rs is not None
        if rule_code in {b["rule"] for b in rs.breakdown}:
            fired = True
    assert fired, f"scenario {tag} did not trigger {rule_code}"


@pytest.mark.parametrize("tag", sorted(MUST_ALERT))
def test_key_scenarios_reach_alert_threshold(scored, tag):
    customers = scored.query(Customer).filter(Customer.scenario_tag == tag).all()
    top = max(
        (_latest_score(scored, c.id).score for c in customers), default=0
    )
    assert top >= 40, f"scenario {tag} scored {top}, below alert threshold"


def test_alerts_created_for_high_risk(scored):
    alerts = scored.query(Alert).all()
    assert len(alerts) >= 6
    # Every alert references at least one triggered rule.
    assert all(a.triggered_rules for a in alerts)


def test_normal_customers_mostly_low_risk(scored):
    normals = scored.query(Customer).filter(Customer.scenario_tag.is_(None)).all()
    low = 0
    for c in normals:
        rs = _latest_score(scored, c.id)
        if rs and rs.risk_level == "low":
            low += 1
    # The clear majority of ordinary customers should be low risk.
    assert low / len(normals) > 0.8
