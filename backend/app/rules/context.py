"""Plain-data context objects passed to the pure rule engine.

The scoring service is responsible for loading ORM rows and flattening them
into these lightweight views, so that rules never import SQLAlchemy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CustomerView:
    id: int
    full_name: str
    occupation: str
    country: str
    is_high_risk_jurisdiction: bool
    date_opened: datetime
    expected_monthly_income: float
    expected_monthly_spend: float


@dataclass
class AccountView:
    id: int
    account_type: str
    opened_at: datetime
    last_activity_at: datetime | None
    is_dormant: bool


@dataclass
class TxnView:
    """A transaction as seen from one customer's perspective."""

    id: int
    external_id: str
    timestamp: datetime
    amount: float
    transaction_type: str
    payment_method: str
    direction: str  # "in" or "out" relative to the customer
    account_id: int  # the customer's account involved
    counterparty_account_id: int | None
    counterparty_customer_id: int | None
    merchant_id: int | None
    merchant_category: str | None
    is_high_risk_merchant: bool
    country: str
    city: str
    latitude: float
    longitude: float


@dataclass
class RuleContext:
    """Everything a rule needs to evaluate one customer. Pure data."""

    customer: CustomerView
    accounts: list[AccountView]
    account_ids: set[int]
    inbound: list[TxnView]  # sorted by timestamp asc
    outbound: list[TxnView]  # sorted by timestamp asc
    located_txns: list[TxnView]  # customer-present txns (card), sorted asc
    now: datetime
    high_risk_countries: set[str]
    # Graph-derived hints (computed once by the service):
    cycles: list[list[int]] = field(default_factory=list)  # customer-id cycles
    cycle_transaction_ids: list[int] = field(default_factory=list)

    @property
    def all_txns(self) -> list[TxnView]:
        return sorted(self.inbound + self.outbound, key=lambda t: t.timestamp)
