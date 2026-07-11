"""Scoring service: bridges the database and the pure rule engine.

Responsibilities:
  * Load ORM rows and flatten them into ``RuleContext`` objects (pure data).
  * Build the global transfer graph once and detect circular rings.
  * Run the engine, persist ``RiskScore`` rows, update customer risk bands,
    and raise ``Alert`` rows above the configured threshold.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.data.reference import HIGH_RISK_COUNTRIES
from app.graph import TransferEdge, cycle_transaction_ids, find_cycles
from app.models import Account, Alert, Customer, RiskScore, Transaction
from app.rules.context import AccountView, CustomerView, RuleContext, TxnView
from app.rules.engine import RuleEngine, ScoreResult
from app.rules.rules import HIGH_RISK_MERCHANT_CATS
from app.services.alert_service import AlertService
from app.utils.enums import PaymentMethod, TransactionType


class ScoringService:
    """Loads context, runs the engine, and persists results."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.engine = RuleEngine()
        self.now = datetime.utcnow()

        # Preloaded lookups (populated by _preload).
        self._customers: list[Customer] = []
        self._accounts_by_customer: dict[int, list[Account]] = {}
        self._account_to_customer: dict[int, int] = {}
        self._inbound: dict[int, list[TxnView]] = {}
        self._outbound: dict[int, list[TxnView]] = {}
        self._located: dict[int, list[TxnView]] = {}
        self._cycles_by_customer: dict[int, list[list[int]]] = {}
        self._cycle_txns_by_customer: dict[int, list[int]] = {}

    # -- public API --------------------------------------------------------

    def score_all(self, raise_alerts: bool = True) -> dict:
        """Score every customer; persist scores and alerts. Idempotent."""
        # Clean slate so re-runs don't duplicate.
        self.db.query(Alert).delete()
        self.db.query(RiskScore).delete()
        self.db.flush()

        self._preload()

        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        alerts_created = 0
        scored: list[tuple[Customer, ScoreResult]] = []

        for customer in self._customers:
            result = self._score_customer(customer)
            distribution[result.risk_level.value] += 1
            scored.append((customer, result))
            if raise_alerts and result.score >= settings.alert_threshold and result.results:
                alert = AlertService.create_from_score(self.db, customer, result)
                # Spread historical alerts over the past ~6 days so the feed
                # shows realistic, staggered timestamps (item 15).
                alert.created_at = self.now - timedelta(
                    minutes=random.randint(2, 6 * 24 * 60)
                )
                alerts_created += 1

        self.db.commit()

        top = sorted(scored, key=lambda x: x[1].score, reverse=True)[:10]
        return {
            "customers_scored": len(scored),
            "distribution": distribution,
            "alerts_created": alerts_created,
            "top_risk": [
                {
                    "customer": c.full_name,
                    "score": r.score,
                    "level": r.risk_level.value,
                    "rules": r.triggered_rule_codes,
                }
                for c, r in top
            ],
        }

    def score_customer(self, customer_id: int) -> ScoreResult:
        """Score a single customer (loads full context; used ad-hoc)."""
        self._preload()
        customer = self.db.get(Customer, customer_id)
        if customer is None:
            raise ValueError(f"Customer {customer_id} not found")
        result = self._score_customer(customer)
        self.db.commit()
        return result

    # -- internals ---------------------------------------------------------

    def _score_customer(self, customer: Customer) -> ScoreResult:
        ctx = self._build_context(customer)
        result = self.engine.evaluate(ctx)

        self.db.add(
            RiskScore(
                customer_id=customer.id,
                score=result.score,
                risk_level=result.risk_level.value,
                breakdown=result.breakdown(),
            )
        )
        customer.risk_level = result.risk_level.value
        return result

    def _build_context(self, customer: Customer) -> RuleContext:
        accounts = self._accounts_by_customer.get(customer.id, [])
        return RuleContext(
            customer=CustomerView(
                id=customer.id,
                full_name=customer.full_name,
                occupation=customer.occupation,
                country=customer.country,
                is_high_risk_jurisdiction=customer.is_high_risk_jurisdiction,
                date_opened=customer.date_opened,
                expected_monthly_income=customer.expected_monthly_income,
                expected_monthly_spend=customer.expected_monthly_spend,
            ),
            accounts=[
                AccountView(
                    id=a.id,
                    account_type=a.account_type,
                    opened_at=a.opened_at,
                    last_activity_at=a.last_activity_at,
                    is_dormant=a.is_dormant,
                )
                for a in accounts
            ],
            account_ids={a.id for a in accounts},
            inbound=self._inbound.get(customer.id, []),
            outbound=self._outbound.get(customer.id, []),
            located_txns=self._located.get(customer.id, []),
            now=self.now,
            high_risk_countries=set(HIGH_RISK_COUNTRIES),
            cycles=self._cycles_by_customer.get(customer.id, []),
            cycle_transaction_ids=self._cycle_txns_by_customer.get(customer.id, []),
        )

    def _preload(self) -> None:
        if self._customers:
            return  # already loaded

        self._customers = self.db.query(Customer).all()
        accounts = self.db.query(Account).all()
        for a in accounts:
            self._accounts_by_customer.setdefault(a.customer_id, []).append(a)
            self._account_to_customer[a.id] = a.customer_id

        transactions = self.db.query(Transaction).order_by(Transaction.timestamp).all()
        edges: list[TransferEdge] = []

        for t in transactions:
            sender_cust = (
                self._account_to_customer.get(t.sender_account_id)
                if t.sender_account_id
                else None
            )
            receiver_cust = (
                self._account_to_customer.get(t.receiver_account_id)
                if t.receiver_account_id
                else None
            )
            is_hr_merchant = (t.merchant_category or "") in HIGH_RISK_MERCHANT_CATS

            # Outbound view for the sending customer.
            if sender_cust is not None:
                view = TxnView(
                    id=t.id,
                    external_id=t.external_id,
                    timestamp=t.timestamp,
                    amount=t.amount,
                    transaction_type=t.transaction_type,
                    payment_method=t.payment_method,
                    direction="out",
                    account_id=t.sender_account_id,
                    counterparty_account_id=t.receiver_account_id,
                    counterparty_customer_id=receiver_cust,
                    merchant_id=t.merchant_id,
                    merchant_category=t.merchant_category,
                    is_high_risk_merchant=is_hr_merchant,
                    country=t.country,
                    city=t.city,
                    latitude=t.latitude,
                    longitude=t.longitude,
                )
                self._outbound.setdefault(sender_cust, []).append(view)
                # Card payments mark the cardholder's physical location.
                if t.payment_method == PaymentMethod.CARD.value:
                    self._located.setdefault(sender_cust, []).append(view)

            # Inbound view for the receiving customer.
            if receiver_cust is not None:
                view = TxnView(
                    id=t.id,
                    external_id=t.external_id,
                    timestamp=t.timestamp,
                    amount=t.amount,
                    transaction_type=t.transaction_type,
                    payment_method=t.payment_method,
                    direction="in",
                    account_id=t.receiver_account_id,
                    counterparty_account_id=t.sender_account_id,
                    counterparty_customer_id=sender_cust,
                    merchant_id=t.merchant_id,
                    merchant_category=t.merchant_category,
                    is_high_risk_merchant=is_hr_merchant,
                    country=t.country,
                    city=t.city,
                    latitude=t.latitude,
                    longitude=t.longitude,
                )
                self._inbound.setdefault(receiver_cust, []).append(view)

            # Transfer edge for the graph (customer -> customer money movement).
            if (
                sender_cust is not None
                and receiver_cust is not None
                and sender_cust != receiver_cust
                and t.transaction_type
                in (TransactionType.TRANSFER.value, TransactionType.WIRE.value)
            ):
                edges.append(
                    TransferEdge(
                        src_customer_id=sender_cust,
                        dst_customer_id=receiver_cust,
                        transaction_id=t.id,
                        amount=t.amount,
                    )
                )

        # Sort the per-customer lists chronologically.
        for mapping in (self._inbound, self._outbound, self._located):
            for lst in mapping.values():
                lst.sort(key=lambda v: v.timestamp)

        # Detect circular rings once, attribute to each member.
        cycles = find_cycles(edges)
        for cycle in cycles:
            txn_ids = cycle_transaction_ids(cycle, edges)
            for member in cycle:
                self._cycles_by_customer.setdefault(member, []).append(cycle)
                self._cycle_txns_by_customer.setdefault(member, []).extend(txn_ids)


