"""Synthetic data generator for Sentinel AML.

Generates a believable synthetic bank: customers, accounts, a merchant catalog,
thousands of ordinary transactions, and a set of *intentionally planted*
money-laundering scenarios that will trip the rule engine during the demo.

The generator is deterministic for a given ``seed`` so the demo is reproducible.

Usage:
    gen = SyntheticDataGenerator(session, seed=42)
    summary = gen.generate()
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from app.data import reference as ref
from app.models import (
    Account,
    Customer,
    Merchant,
    Relationship,
    Transaction,
)
from app.utils.enums import (
    AccountType,
    KycStatus,
    PaymentMethod,
    RelationshipType,
    RiskLevel,
    ScenarioTag,
    TransactionType,
)

# Tunable volumes ----------------------------------------------------------
NUM_CUSTOMERS = 150
NORMAL_TXNS_PER_CUSTOMER = (12, 40)  # (min, max) ordinary transactions each
HISTORY_DAYS = 270  # ~9 months of history


@dataclass
class GenerationSummary:
    """Row counts + planted-scenario report returned after generation."""

    customers: int = 0
    accounts: int = 0
    merchants: int = 0
    transactions: int = 0
    relationships: int = 0
    scenarios: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "customers": self.customers,
            "accounts": self.accounts,
            "merchants": self.merchants,
            "transactions": self.transactions,
            "relationships": self.relationships,
            "scenarios": self.scenarios,
        }


class SyntheticDataGenerator:
    """Builds the full synthetic dataset inside a SQLAlchemy session."""

    def __init__(self, session: Session, seed: int = 42) -> None:
        self.db = session
        self.seed = seed
        self.rng = random.Random(seed)
        self.faker = Faker()
        Faker.seed(seed)

        self.now = datetime.utcnow()
        self._txn_counter = 0

        self.merchants: list[Merchant] = []
        self.customers: list[Customer] = []
        # customer_id -> {account_type: Account}
        self.accounts_by_customer: dict[int, dict[str, Account]] = {}
        self.summary = GenerationSummary()

    # -- public API --------------------------------------------------------

    def generate(self) -> GenerationSummary:
        """Generate the entire dataset and flush it to the session."""
        self._generate_merchants()
        self._generate_customers()
        self.db.flush()  # assign IDs to customers/accounts
        self._index_accounts()

        # Ordinary activity for every customer.
        for customer in self.customers:
            self._generate_normal_activity(customer)

        # Planted laundering scenarios (each returns a short description).
        self._plant_scenarios()

        self.db.flush()
        self._finalize_summary()
        return self.summary

    # -- merchants ---------------------------------------------------------

    def _generate_merchants(self) -> None:
        # A few merchants per category for variety.
        for category, mcc, is_high_risk in ref.MERCHANT_CATEGORIES:
            count = 2 if is_high_risk else 3
            for _ in range(count):
                city = self.rng.choice(list(ref.LOCATIONS.keys()))
                country, _lat, _lon = ref.LOCATIONS[city]
                hint = self.rng.choice(ref.MERCHANT_NAME_HINTS[category])
                name = f"{self.faker.last_name()} {hint}"
                merchant = Merchant(
                    name=name,
                    category=category,
                    country=country,
                    city=city,
                    mcc=mcc,
                    is_high_risk=is_high_risk,
                )
                self.db.add(merchant)
                self.merchants.append(merchant)

    def _merchants_in(self, category: str) -> list[Merchant]:
        return [m for m in self.merchants if m.category == category]

    def _normal_merchant(self) -> Merchant:
        pool = [m for m in self.merchants if not m.is_high_risk]
        return self.rng.choice(pool)

    # -- customers + accounts ---------------------------------------------

    def _generate_customers(self) -> None:
        # Reserve slots: the last N customers become scenario "heroes".
        scenario_tags = [
            ScenarioTag.STRUCTURING,
            ScenarioTag.RAPID_MOVEMENT,
            ScenarioTag.CIRCULAR_RING,  # A
            ScenarioTag.CIRCULAR_RING,  # B
            ScenarioTag.CIRCULAR_RING,  # C
            ScenarioTag.DORMANT_AWAKENING,
            ScenarioTag.VELOCITY_BURST,
            ScenarioTag.GEO_ANOMALY,
            ScenarioTag.MONEY_MULE,
            ScenarioTag.CRYPTO_LAYERING,
            ScenarioTag.ACCOUNT_EXPLOSION,
        ]
        # Randomize the normal-customer count so each seed differs (item 8).
        num_normal = self.rng.randint(240, 330)

        for _ in range(num_normal):
            self._create_customer(scenario_tag=None)
        for tag in scenario_tags:
            self._create_customer(scenario_tag=tag)

    def _create_customer(self, scenario_tag: ScenarioTag | None) -> Customer:
        occupation, base_income = self.rng.choice(ref.OCCUPATIONS)
        income = base_income * self.rng.uniform(0.8, 1.3)

        # Most customers are domestic + verified; some are international.
        if self.rng.random() < 0.75:
            city = self.rng.choice(ref.US_CITIES)
        else:
            city = self.rng.choice(ref.INTL_CITIES + ref.HIGH_RISK_CITIES)
        country, _lat, _lon = ref.LOCATIONS[city]

        is_high_risk_jur = country in ref.HIGH_RISK_COUNTRIES
        date_opened = self.now - timedelta(
            days=self.rng.randint(400, 3200)
        )

        monthly_income = income / 12.0
        monthly_spend = monthly_income * self.rng.uniform(0.5, 0.85)

        kyc = self.rng.choices(
            [KycStatus.VERIFIED, KycStatus.PENDING, KycStatus.REJECTED],
            weights=[0.86, 0.11, 0.03],
        )[0]

        customer = Customer(
            full_name=self.faker.name(),
            occupation=occupation,
            country=country,
            city=city,
            annual_income=round(income, 2),
            expected_monthly_income=round(monthly_income, 2),
            expected_monthly_spend=round(monthly_spend, 2),
            risk_level=RiskLevel.LOW.value,
            kyc_status=kyc.value,
            is_high_risk_jurisdiction=is_high_risk_jur,
            date_opened=date_opened,
            scenario_tag=scenario_tag.value if scenario_tag else None,
        )
        self.db.add(customer)
        self.customers.append(customer)

        # Accounts: checking + savings always; business sometimes.
        self._create_account(customer, AccountType.CHECKING, date_opened)
        self._create_account(customer, AccountType.SAVINGS, date_opened)
        business_occ = occupation in {
            "Small Business Owner",
            "Restaurant Owner",
            "Import/Export Trader",
            "Jewelry Dealer",
            "Art Dealer",
            "Consultant",
        }
        if business_occ or self.rng.random() < 0.15:
            self._create_account(customer, AccountType.BUSINESS, date_opened)

        return customer

    def _create_account(
        self, customer: Customer, account_type: AccountType, opened_at: datetime
    ) -> Account:
        balance = {
            AccountType.CHECKING: self.rng.uniform(1_500, 25_000),
            AccountType.SAVINGS: self.rng.uniform(5_000, 120_000),
            AccountType.BUSINESS: self.rng.uniform(10_000, 250_000),
        }[account_type]

        account = Account(
            customer=customer,
            account_number=self._account_number(),
            account_type=account_type.value,
            currency="USD",
            balance=round(balance, 2),
            opened_at=opened_at,
            last_activity_at=self.now - timedelta(days=self.rng.randint(0, 20)),
            is_dormant=False,
        )
        self.db.add(account)
        return account

    def _index_accounts(self) -> None:
        for customer in self.customers:
            self.accounts_by_customer[customer.id] = {
                acc.account_type: acc for acc in customer.accounts
            }

    def _primary_account(self, customer: Customer) -> Account:
        return self.accounts_by_customer[customer.id][AccountType.CHECKING.value]

    # -- normal activity ---------------------------------------------------

    def _generate_normal_activity(self, customer: Customer) -> None:
        checking = self._primary_account(customer)
        n = self.rng.randint(*NORMAL_TXNS_PER_CUSTOMER)
        monthly_spend = customer.expected_monthly_spend

        # Monthly salary deposits.
        months = HISTORY_DAYS // 30
        for m in range(months):
            ts = self.now - timedelta(days=HISTORY_DAYS - m * 30, hours=self.rng.randint(0, 12))
            self._add_transaction(
                receiver=checking,
                sender=None,
                merchant=None,
                amount=round(customer.expected_monthly_income * self.rng.uniform(0.95, 1.05), 2),
                ttype=TransactionType.DEPOSIT,
                method=PaymentMethod.ACH,
                timestamp=ts,
                city=customer.city,
            )

        # Everyday card spend at merchants.
        for _ in range(n):
            merchant = self._normal_merchant()
            amount = round(
                max(5.0, self.rng.gauss(monthly_spend / 12.0, monthly_spend / 20.0)),
                2,
            )
            ts = self.now - timedelta(
                days=self.rng.randint(0, HISTORY_DAYS),
                hours=self.rng.randint(0, 23),
                minutes=self.rng.randint(0, 59),
            )
            self._add_transaction(
                sender=checking,
                receiver=None,
                merchant=merchant,
                amount=amount,
                ttype=TransactionType.PAYMENT,
                method=PaymentMethod.CARD,
                timestamp=ts,
                city=customer.city,
            )

        # Occasional peer transfer to another random customer.
        if self.rng.random() < 0.5:
            other = self.rng.choice(self.customers)
            if other.id != customer.id:
                self._add_transaction(
                    sender=checking,
                    receiver=self._primary_account(other),
                    merchant=None,
                    amount=round(self.rng.uniform(50, 1500), 2),
                    ttype=TransactionType.TRANSFER,
                    method=PaymentMethod.ACH,
                    timestamp=self.now - timedelta(days=self.rng.randint(0, HISTORY_DAYS)),
                    city=customer.city,
                )

        self._inject_minor_risk(customer, checking)

    def _inject_minor_risk(self, customer: Customer, checking: Account) -> None:
        """Give a random subset of ordinary customers small risk signals so the
        population shows a natural spread of no / small / medium risk instead of
        everyone sitting at zero (items 6-7)."""
        roll = self.rng.random()
        tier = 0
        if roll < 0.30:
            tier = 1  # one minor signal -> low band
        elif roll < 0.38:
            tier = 2  # two minor signals -> medium band
        if tier == 0:
            return

        signals = self.rng.sample(["cash", "geo", "highrisk"], k=tier)
        base = self.now - timedelta(days=self.rng.randint(1, 60))
        for sig in signals:
            if sig == "cash":
                self._add_transaction(
                    receiver=checking, sender=None, merchant=None,
                    amount=round(self.rng.uniform(10_500, 13_500), 2),
                    ttype=TransactionType.DEPOSIT, method=PaymentMethod.CASH,
                    timestamp=base - timedelta(hours=self.rng.randint(1, 200)),
                    city=customer.city,
                )
            elif sig == "geo":
                a = base - timedelta(days=self.rng.randint(1, 20))
                self._add_transaction(
                    sender=checking, receiver=None,
                    merchant=self.rng.choice(self._merchants_in("retail")),
                    amount=round(self.rng.uniform(60, 400), 2),
                    ttype=TransactionType.PAYMENT, method=PaymentMethod.CARD,
                    timestamp=a, city="Miami",
                )
                self._add_transaction(
                    sender=checking, receiver=None,
                    merchant=self.rng.choice(self._merchants_in("electronics")),
                    amount=round(self.rng.uniform(60, 400), 2),
                    ttype=TransactionType.PAYMENT, method=PaymentMethod.CARD,
                    timestamp=a + timedelta(minutes=self.rng.randint(12, 40)),
                    city="Tokyo",
                )
            elif sig == "highrisk":
                self._add_transaction(
                    sender=checking, receiver=None,
                    merchant=self.rng.choice(self._merchants_in("retail")),
                    amount=round(self.rng.uniform(80, 600), 2),
                    ttype=TransactionType.PAYMENT, method=PaymentMethod.CARD,
                    timestamp=base - timedelta(hours=self.rng.randint(1, 300)),
                    city=self.rng.choice(ref.HIGH_RISK_CITIES),
                )

    # -- planted scenarios -------------------------------------------------

    def _plant_scenarios(self) -> None:
        by_tag: dict[str, list[Customer]] = {}
        for c in self.customers:
            if c.scenario_tag:
                by_tag.setdefault(c.scenario_tag, []).append(c)

        self._scenario_structuring(by_tag[ScenarioTag.STRUCTURING.value][0])
        self._scenario_rapid_movement(by_tag[ScenarioTag.RAPID_MOVEMENT.value][0])
        self._scenario_circular_ring(by_tag[ScenarioTag.CIRCULAR_RING.value])
        self._scenario_dormant(by_tag[ScenarioTag.DORMANT_AWAKENING.value][0])
        self._scenario_velocity(by_tag[ScenarioTag.VELOCITY_BURST.value][0])
        self._scenario_geo_anomaly(by_tag[ScenarioTag.GEO_ANOMALY.value][0])
        self._scenario_money_mule(by_tag[ScenarioTag.MONEY_MULE.value][0])
        self._scenario_crypto_layering(by_tag[ScenarioTag.CRYPTO_LAYERING.value][0])
        self._scenario_account_explosion(by_tag[ScenarioTag.ACCOUNT_EXPLOSION.value][0])

    def _scenario_structuring(self, customer: Customer) -> None:
        """Repeated cash deposits just below the $10k reporting threshold."""
        checking = self._primary_account(customer)
        start = self.now - timedelta(days=14)
        for i in range(9):
            amount = round(self.rng.uniform(9_000, 9_900), 2)
            ts = start + timedelta(days=i * self.rng.choice([1, 2]), hours=self.rng.randint(9, 17))
            self._add_transaction(
                receiver=checking,
                sender=None,
                merchant=None,
                amount=amount,
                ttype=TransactionType.DEPOSIT,
                method=PaymentMethod.CASH,
                timestamp=ts,
                city=customer.city,
                flagged=True,
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: 9 cash deposits of $9,000-$9,900 over 2 weeks"
        )

    def _scenario_rapid_movement(self, customer: Customer) -> None:
        """Large funds enter then leave within 2 hours."""
        checking = self._primary_account(customer)
        counterparties = self._random_other_customers(customer, 3)
        for i in range(3):
            base = self.now - timedelta(days=self.rng.randint(2, 20))
            inbound = round(self.rng.uniform(40_000, 90_000), 2)
            self._add_transaction(
                receiver=checking,
                sender=None,
                merchant=None,
                amount=inbound,
                ttype=TransactionType.WIRE,
                method=PaymentMethod.WIRE,
                timestamp=base,
                city=customer.city,
                flagged=True,
            )
            # Money leaves within ~30-90 minutes.
            out_ts = base + timedelta(minutes=self.rng.randint(20, 90))
            self._add_transaction(
                sender=checking,
                receiver=self._primary_account(counterparties[i]),
                merchant=None,
                amount=round(inbound * self.rng.uniform(0.9, 0.98), 2),
                ttype=TransactionType.TRANSFER,
                method=PaymentMethod.WIRE,
                timestamp=out_ts,
                city=customer.city,
                flagged=True,
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: 3 large wires withdrawn within ~1h of arrival"
        )

    def _scenario_circular_ring(self, members: list[Customer]) -> None:
        """A -> B -> C -> A circular transfer loop."""
        members = members[:3]
        if len(members) < 3:
            return
        amount = round(self.rng.uniform(60_000, 85_000), 2)
        base = self.now - timedelta(days=self.rng.randint(3, 15))
        for i, member in enumerate(members):
            nxt = members[(i + 1) % len(members)]
            self._add_transaction(
                sender=self._primary_account(member),
                receiver=self._primary_account(nxt),
                merchant=None,
                amount=round(amount * self.rng.uniform(0.95, 1.0), 2),
                ttype=TransactionType.TRANSFER,
                method=PaymentMethod.WIRE,
                timestamp=base + timedelta(hours=i * self.rng.randint(2, 8)),
                city=member.city,
                flagged=True,
            )
            # Relationship edge marks the ring.
            self.db.add(
                Relationship(
                    source_customer_id=member.id,
                    target_customer_id=nxt.id,
                    relationship_type=RelationshipType.RING.value,
                    strength=amount,
                )
            )
        names = " -> ".join(m.full_name for m in members)
        self.summary.scenarios[ScenarioTag.CIRCULAR_RING.value] = (
            f"Ring: {names} -> back to start (~${amount:,.0f} loop)"
        )

    def _scenario_dormant(self, customer: Customer) -> None:
        """Account inactive 6+ months then a sudden large inbound wire."""
        savings = self.accounts_by_customer[customer.id][AccountType.SAVINGS.value]
        # Force dormancy: last activity 7 months ago.
        savings.last_activity_at = self.now - timedelta(days=210)
        savings.is_dormant = True
        # Old small activity, then a big recent wire.
        self._add_transaction(
            receiver=savings,
            sender=None,
            merchant=None,
            amount=round(self.rng.uniform(150, 400), 2),
            ttype=TransactionType.DEPOSIT,
            method=PaymentMethod.ACH,
            timestamp=self.now - timedelta(days=230),
            city=customer.city,
        )
        self._add_transaction(
            receiver=savings,
            sender=None,
            merchant=None,
            amount=round(self.rng.uniform(120_000, 220_000), 2),
            ttype=TransactionType.WIRE,
            method=PaymentMethod.WIRE,
            timestamp=self.now - timedelta(days=2),
            city=customer.city,
            flagged=True,
        )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: dormant 7 months, then a sudden ~$150k+ wire"
        )

    def _scenario_velocity(self, customer: Customer) -> None:
        """Many transfers within minutes."""
        checking = self._primary_account(customer)
        others = self._random_other_customers(customer, 12)
        base = self.now - timedelta(days=self.rng.randint(1, 6), hours=3)
        for i, other in enumerate(others):
            self._add_transaction(
                sender=checking,
                receiver=self._primary_account(other),
                merchant=None,
                amount=round(self.rng.uniform(2_000, 6_000), 2),
                ttype=TransactionType.TRANSFER,
                method=PaymentMethod.ACH,
                timestamp=base + timedelta(minutes=i * self.rng.randint(1, 3)),
                city=customer.city,
                flagged=True,
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: 12 transfers within a few minutes"
        )

    def _scenario_geo_anomaly(self, customer: Customer) -> None:
        """Card use in impossible location pairs (Miami then Tokyo 15 min later)."""
        checking = self._primary_account(customer)
        base = self.now - timedelta(days=self.rng.randint(1, 10))
        pairs = [("Miami", "Tokyo"), ("Los Angeles", "Dubai")]
        for j, (city_a, city_b) in enumerate(pairs):
            offset = timedelta(days=j)
            self._add_transaction(
                sender=checking,
                receiver=None,
                merchant=self.rng.choice(self._merchants_in("retail")),
                amount=round(self.rng.uniform(200, 900), 2),
                ttype=TransactionType.PAYMENT,
                method=PaymentMethod.CARD,
                timestamp=base + offset,
                city=city_a,
                flagged=True,
            )
            self._add_transaction(
                sender=checking,
                receiver=None,
                merchant=self.rng.choice(self._merchants_in("electronics")),
                amount=round(self.rng.uniform(200, 900), 2),
                ttype=TransactionType.PAYMENT,
                method=PaymentMethod.CARD,
                timestamp=base + offset + timedelta(minutes=15),
                city=city_b,
                flagged=True,
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: card used in Miami then Tokyo 15 min later"
        )

    def _scenario_money_mule(self, customer: Customer) -> None:
        """20+ unrelated accounts funnel money into one account."""
        checking = self._primary_account(customer)
        senders = self._random_other_customers(customer, 22)
        base = self.now - timedelta(days=self.rng.randint(2, 9))
        for i, sender in enumerate(senders):
            self._add_transaction(
                sender=self._primary_account(sender),
                receiver=checking,
                merchant=None,
                amount=round(self.rng.uniform(1_500, 4_500), 2),
                ttype=TransactionType.TRANSFER,
                method=PaymentMethod.ACH,
                timestamp=base + timedelta(hours=i * self.rng.uniform(0.5, 3.0)),
                city=sender.city,
                flagged=True,
            )
            self.db.add(
                Relationship(
                    source_customer_id=sender.id,
                    target_customer_id=customer.id,
                    relationship_type=RelationshipType.TRANSFER.value,
                    strength=1.0,
                )
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: 22 unrelated senders funneling funds in"
        )

    def _scenario_crypto_layering(self, customer: Customer) -> None:
        """Rapid layering through crypto exchanges + high-risk jurisdictions."""
        checking = self._primary_account(customer)
        crypto = self._merchants_in("crypto_exchange")
        base = self.now - timedelta(days=self.rng.randint(1, 8))
        # Big inbound wire from a high-risk city, then rapid crypto purchases.
        hr_city = self.rng.choice(ref.HIGH_RISK_CITIES)
        self._add_transaction(
            receiver=checking,
            sender=None,
            merchant=None,
            amount=round(self.rng.uniform(70_000, 130_000), 2),
            ttype=TransactionType.WIRE,
            method=PaymentMethod.WIRE,
            timestamp=base,
            city=hr_city,
            flagged=True,
        )
        for i in range(6):
            self._add_transaction(
                sender=checking,
                receiver=None,
                merchant=self.rng.choice(crypto),
                amount=round(self.rng.uniform(8_000, 18_000), 2),
                ttype=TransactionType.PAYMENT,
                method=PaymentMethod.CRYPTO,
                timestamp=base + timedelta(minutes=15 + i * self.rng.randint(5, 20)),
                city=customer.city,
                flagged=True,
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: high-risk wire layered through crypto exchanges"
        )

    def _scenario_account_explosion(self, customer: Customer) -> None:
        """A newly opened account receives unusually large volume fast."""
        # Re-open the customer very recently.
        recent = self.now - timedelta(days=9)
        customer.date_opened = recent
        checking = self._primary_account(customer)
        checking.opened_at = recent
        senders = self._random_other_customers(customer, 10)
        for i, sender in enumerate(senders):
            self._add_transaction(
                sender=self._primary_account(sender),
                receiver=checking,
                merchant=None,
                amount=round(self.rng.uniform(15_000, 40_000), 2),
                ttype=TransactionType.WIRE,
                method=PaymentMethod.WIRE,
                timestamp=recent + timedelta(days=self.rng.uniform(0.2, 8.0)),
                city=sender.city,
                flagged=True,
            )
        self.summary.scenarios[customer.scenario_tag] = (
            f"{customer.full_name}: 9-day-old account receiving ~$200k+ in wires"
        )

    # -- transaction helper ------------------------------------------------

    def _add_transaction(
        self,
        *,
        amount: float,
        ttype: TransactionType,
        method: PaymentMethod,
        timestamp: datetime,
        city: str,
        sender: Account | None = None,
        receiver: Account | None = None,
        merchant: Merchant | None = None,
        flagged: bool = False,
    ) -> Transaction:
        country, lat, lon = ref.LOCATIONS.get(
            city, (self.rng.choice(list(ref.LOCATIONS.values()))[0], 0.0, 0.0)
        )
        # Small jitter so points aren't perfectly stacked on the heatmap.
        lat += self.rng.uniform(-0.05, 0.05)
        lon += self.rng.uniform(-0.05, 0.05)

        # Second-level jitter so timestamps aren't aligned to whole minutes.
        timestamp = timestamp + timedelta(
            seconds=self.rng.randint(0, 59), microseconds=self.rng.randint(0, 999_999)
        )

        self._txn_counter += 1
        txn = Transaction(
            external_id=f"TXN-{self._txn_counter:07d}",
            timestamp=timestamp,
            sender_account_id=sender.id if sender else None,
            receiver_account_id=receiver.id if receiver else None,
            merchant_id=merchant.id if merchant else None,
            transaction_type=ttype.value,
            payment_method=method.value,
            merchant_category=merchant.category if merchant else None,
            amount=amount,
            currency="USD",
            country=country,
            city=city,
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            device_id=self.faker.uuid4(),
            ip_address=self.faker.ipv4_public(),
            is_flagged=flagged,
        )
        self.db.add(txn)
        return txn

    # -- misc helpers ------------------------------------------------------

    def _random_other_customers(self, customer: Customer, k: int) -> list[Customer]:
        pool = [c for c in self.customers if c.id != customer.id and not c.scenario_tag]
        self.rng.shuffle(pool)
        return pool[:k]

    def _account_number(self) -> str:
        return "".join(self.rng.choice("0123456789") for _ in range(12))

    def _finalize_summary(self) -> None:
        self.summary.customers = len(self.customers)
        self.summary.accounts = sum(len(c.accounts) for c in self.customers)
        self.summary.merchants = len(self.merchants)
        self.summary.transactions = self._txn_counter
        self.summary.relationships = self.db.query(Relationship).count()
