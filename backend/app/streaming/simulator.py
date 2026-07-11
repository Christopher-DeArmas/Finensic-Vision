"""Real-time synthetic transaction simulator.

A background asyncio task emits 2-5 transactions per second. Most are ordinary;
a fraction are engineered to look suspicious (structuring, high-risk wires,
crypto layering, large transfers) and are flagged. Each transaction is
persisted, suspicious ones trigger a scoped rescore of the involved customer
(which may raise an alert), and every event is broadcast to WebSocket clients.

DB work runs in a worker thread (``asyncio.to_thread``) so the event loop stays
responsive.
"""

from __future__ import annotations

import asyncio
import logging
import random
import uuid
from datetime import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.data import reference as ref
from app.models import Account, Alert, Customer, Merchant, Transaction
from app.services.alert_service import AlertService
from app.streaming.connection_manager import ConnectionManager
from app.streaming.scoring import score_customer_scoped
from app.utils.enums import PaymentMethod, TransactionType

logger = logging.getLogger("sentinel.streaming")

SUSPICIOUS_RATE = 0.15


class TransactionSimulator:
    def __init__(self, manager: ConnectionManager) -> None:
        self.manager = manager
        self.rng = random.Random()
        self._task: asyncio.Task | None = None
        self._running = False
        # Snapshot of accounts/merchants (loaded once; static during streaming).
        self._accounts: list[tuple[int, int, str]] = []  # (id, customer_id, name)
        self._merchants: list[tuple[int, str, bool, str]] = []  # (id, category, hr, name)
        self._account_name: dict[int, str] = {}
        self._merchant_name: dict[int, str] = {}
        # Seed risk band per customer + how many live suspicious events each has
        # absorbed — used to keep the majority of customers inside their band.
        self._cust_band: dict[int, str] = {}
        self._suspicious_count: dict[int, int] = {}
        self.emitted = 0

    # -- lifecycle ---------------------------------------------------------

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Transaction simulator started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Transaction simulator stopped")

    async def _run(self) -> None:
        while self._running:
            tps = self.rng.uniform(settings.stream_min_tps, settings.stream_max_tps)
            await asyncio.sleep(1.0 / max(tps, 0.1))
            try:
                events = await asyncio.to_thread(self._tick)
            except Exception:  # noqa: BLE001 - keep the stream alive
                logger.exception("simulator tick failed")
                continue
            for event in events:
                await self.manager.broadcast(event)

    # -- generation (runs in a worker thread) ------------------------------

    def _ensure_snapshot(self, db) -> bool:
        if self._accounts:
            return True
        rows = (
            db.query(
                Account.id, Account.customer_id, Customer.full_name, Customer.risk_level
            )
            .join(Customer, Account.customer_id == Customer.id)
            .all()
        )
        self._accounts = [(a, c, n) for a, c, n, _ in rows]
        self._account_name = {a: n for a, c, n, _ in rows}
        self._cust_band = {c: (lvl or "low") for _a, c, _n, lvl in rows}
        mrows = db.query(Merchant.id, Merchant.category, Merchant.is_high_risk, Merchant.name).all()
        self._merchants = [(i, cat, hr, nm) for i, cat, hr, nm in mrows]
        self._merchant_name = {i: nm for i, cat, hr, nm in mrows}
        return bool(self._accounts)

    def _tick(self) -> list[dict]:
        db = SessionLocal()
        try:
            if not self._ensure_snapshot(db):
                return []
            suspicious = self.rng.random() < SUSPICIOUS_RATE
            txn, subject_customer_id = (
                self._make_suspicious(db) if suspicious else self._make_normal(db)
            )
            db.add(txn)
            db.commit()
            db.refresh(txn)
            self.emitted += 1

            events = [self._txn_event(txn)]

            if suspicious and subject_customer_id is not None:
                alert_event = self._maybe_alert(db, subject_customer_id, txn)
                if alert_event:
                    events.append(alert_event)
            return events
        finally:
            db.close()

    # -- transaction builders ----------------------------------------------

    def _loc(self, city: str) -> tuple[str, float, float]:
        country, lat, lon = ref.LOCATIONS[city]
        return country, lat + self.rng.uniform(-0.05, 0.05), lon + self.rng.uniform(-0.05, 0.05)

    def _new_txn(self, **kw) -> Transaction:
        city = kw.pop("city")
        country, lat, lon = self._loc(city)
        return Transaction(
            external_id=f"LIVE-{uuid.uuid4().hex[:10]}",
            timestamp=datetime.utcnow(),
            currency="USD",
            country=country,
            city=city,
            latitude=round(lat, 6),
            longitude=round(lon, 6),
            device_id=uuid.uuid4().hex,
            ip_address=f"{self.rng.randint(11,240)}.{self.rng.randint(0,255)}."
            f"{self.rng.randint(0,255)}.{self.rng.randint(1,254)}",
            **kw,
        )

    def _city(self) -> str:
        """A globally spread city (mostly US, some international / high-risk)."""
        r = self.rng.random()
        if r < 0.5:
            return self.rng.choice(ref.US_CITIES)
        if r < 0.88:
            return self.rng.choice(ref.INTL_CITIES)
        return self.rng.choice(ref.HIGH_RISK_CITIES)

    # Selection weight by seed band + a decay so no single customer absorbs an
    # unbounded number of live suspicious events. This keeps the majority of
    # low / medium / high customers inside their original band over time and
    # makes a 100/100 score rare (items 1-3, 8).
    _BAND_WEIGHT = {"low": 0.10, "medium": 0.55, "high": 1.8, "critical": 1.0}
    # Max number of live suspicious events that may rescore (and thus possibly
    # escalate) a single customer before their band is frozen.
    ESCALATE_CAP = 3

    def _suspicious_account(self) -> tuple[int, int]:
        """Pick the subject of a suspicious transaction, biased toward
        already-risky customers and away from anyone who has already absorbed
        several live suspicious events."""
        weights = []
        for _aid, cust, _n in self._accounts:
            w = self._BAND_WEIGHT.get(self._cust_band.get(cust, "low"), 0.4)
            w *= max(0.05, 1.0 - 0.30 * self._suspicious_count.get(cust, 0))
            weights.append(w)
        aid, cust, _n = self.rng.choices(self._accounts, weights=weights, k=1)[0]
        self._suspicious_count[cust] = self._suspicious_count.get(cust, 0) + 1
        return aid, cust

    def _other_account(self, exclude_aid: int) -> int:
        aid = exclude_aid
        while aid == exclude_aid:
            aid = self.rng.choice(self._accounts)[0]
        return aid

    def _make_normal(self, db) -> tuple[Transaction, int | None]:
        kind = self.rng.random()
        if kind < 0.6:  # card payment at a merchant
            aid, cust, _ = self.rng.choice(self._accounts)
            mid, cat, _hr, _nm = self.rng.choice(self._merchants)
            txn = self._new_txn(
                sender_account_id=aid, merchant_id=mid, merchant_category=cat,
                transaction_type=TransactionType.PAYMENT.value,
                payment_method=PaymentMethod.CARD.value,
                amount=round(self.rng.uniform(8, 400), 2),
                city=self._city(), is_flagged=False,
            )
            return txn, cust
        # peer transfer
        (a1, c1, _), (a2, _c2, _) = self.rng.sample(self._accounts, 2)
        txn = self._new_txn(
            sender_account_id=a1, receiver_account_id=a2,
            transaction_type=TransactionType.TRANSFER.value,
            payment_method=PaymentMethod.ACH.value,
            amount=round(self.rng.uniform(50, 1800), 2),
            city=self._city(), is_flagged=False,
        )
        return txn, c1

    def _make_suspicious(self, db) -> tuple[Transaction, int | None]:
        choice = self.rng.choice(
            ["structuring", "high_risk_wire", "crypto", "large_transfer"]
        )
        if choice == "structuring":
            aid, cust = self._suspicious_account()
            txn = self._new_txn(
                receiver_account_id=aid,
                transaction_type=TransactionType.DEPOSIT.value,
                payment_method=PaymentMethod.CASH.value,
                amount=round(self.rng.uniform(9000, 9900), 2),
                city=self._city(), is_flagged=True,
            )
            return txn, cust
        if choice == "high_risk_wire":
            aid, cust = self._suspicious_account()
            txn = self._new_txn(
                receiver_account_id=aid,
                transaction_type=TransactionType.WIRE.value,
                payment_method=PaymentMethod.WIRE.value,
                amount=round(self.rng.uniform(30000, 95000), 2),
                city=self.rng.choice(ref.HIGH_RISK_CITIES), is_flagged=True,
            )
            return txn, cust
        if choice == "crypto":
            aid, cust = self._suspicious_account()
            crypto = [m for m in self._merchants if m[1] == "crypto_exchange"]
            mid, cat, _hr, _nm = self.rng.choice(crypto) if crypto else self.rng.choice(self._merchants)
            txn = self._new_txn(
                sender_account_id=aid, merchant_id=mid, merchant_category=cat,
                transaction_type=TransactionType.PAYMENT.value,
                payment_method=PaymentMethod.CRYPTO.value,
                amount=round(self.rng.uniform(8000, 20000), 2),
                city=self._city(), is_flagged=True,
            )
            return txn, cust
        # large_transfer
        a1, c1 = self._suspicious_account()
        a2 = self._other_account(a1)
        txn = self._new_txn(
            sender_account_id=a1, receiver_account_id=a2,
            transaction_type=TransactionType.TRANSFER.value,
            payment_method=PaymentMethod.WIRE.value,
            amount=round(self.rng.uniform(20000, 60000), 2),
            city=self._city(), is_flagged=True,
        )
        return txn, c1

    # -- alerts + payloads -------------------------------------------------

    def _maybe_alert(self, db, customer_id: int, txn: Transaction) -> dict | None:
        # Keep the overall band distribution stable over long runs: the live
        # rescore is what moves a customer between bands, so never let it
        # escalate a seed low-risk customer, and cap how many live suspicious
        # events can rescore any single customer. The transaction is still
        # shown in the feed / heatmap regardless (items 1-3, 8).
        band = self._cust_band.get(customer_id, "low")
        if band == "low" or self._suspicious_count.get(customer_id, 0) > self.ESCALATE_CAP:
            return None
        # Avoid alert spam: only if the customer has no currently-open alert.
        existing = (
            db.query(Alert)
            .filter(Alert.customer_id == customer_id, Alert.status == "open")
            .first()
        )
        if existing is not None:
            return None
        result = score_customer_scoped(db, customer_id)
        if result is None or result.score < settings.alert_threshold or not result.results:
            db.commit()
            return None
        customer = db.get(Customer, customer_id)
        # Link this live transaction as evidence too.
        alert = AlertService.create_from_score(db, customer, result)
        if txn not in alert.transactions:
            alert.transactions.append(txn)
        db.commit()
        db.refresh(alert)
        return {
            "type": "alert",
            "data": {
                "id": alert.id,
                "customer_id": customer.id,
                "customer_name": customer.full_name,
                "severity": alert.severity,
                "score": alert.score,
                "title": alert.title,
                "triggered_rules": alert.triggered_rules,
                "created_at": alert.created_at.isoformat() if alert.created_at else None,
            },
        }

    def _txn_event(self, txn: Transaction) -> dict:
        return {
            "type": "transaction",
            "data": {
                "external_id": txn.external_id,
                "timestamp": txn.timestamp.isoformat(),
                "amount": txn.amount,
                "currency": txn.currency,
                "transaction_type": txn.transaction_type,
                "payment_method": txn.payment_method,
                "country": txn.country,
                "city": txn.city,
                "latitude": txn.latitude,
                "longitude": txn.longitude,
                "is_flagged": txn.is_flagged,
                "sender_name": self._account_name.get(txn.sender_account_id),
                "receiver_name": self._account_name.get(txn.receiver_account_id),
                "merchant_name": self._merchant_name.get(txn.merchant_id),
            },
        }
