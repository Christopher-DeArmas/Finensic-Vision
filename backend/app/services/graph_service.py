"""Builds a customer's transaction-network graph for visualization.

Produces an ego-network: the subject customer at the center, connected to the
counterparty customers they moved money with and the merchants they paid.
Edges aggregate the underlying transactions; an edge is "suspicious" if any of
its transactions were rule-flagged.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Account, Customer, Merchant, Transaction
from app.rules.rules import HIGH_RISK_MERCHANT_CATS
from app.schemas.graph import GraphData, GraphEdge, GraphNode
from app.utils.enums import TransactionType

MAX_MERCHANTS = 8


@dataclass
class _Agg:
    inbound: float = 0.0  # counterparty -> subject
    outbound: float = 0.0  # subject -> counterparty
    count: int = 0
    suspicious: bool = False
    label: str = ""
    risk_level: str | None = None
    is_high_risk: bool = False
    kind: str = "customer"
    txn_ids: list = field(default_factory=list)

    @property
    def total(self) -> float:
        return self.inbound + self.outbound


def build_customer_graph(db: Session, customer_id: int) -> GraphData | None:
    subject = db.get(Customer, customer_id)
    if subject is None:
        return None

    accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
    acc_ids = {a.id for a in accounts}
    if not acc_ids:
        return GraphData(nodes=[], edges=[])

    txns = (
        db.query(Transaction)
        .filter(
            or_(
                Transaction.sender_account_id.in_(acc_ids),
                Transaction.receiver_account_id.in_(acc_ids),
            )
        )
        .all()
    )

    # Resolve counterparty accounts -> their owning customer.
    other_accounts = set()
    for t in txns:
        if t.sender_account_id and t.sender_account_id not in acc_ids:
            other_accounts.add(t.sender_account_id)
        if t.receiver_account_id and t.receiver_account_id not in acc_ids:
            other_accounts.add(t.receiver_account_id)
    acc_to_cust: dict[int, int] = {}
    if other_accounts:
        for aid, cid in db.query(Account.id, Account.customer_id).filter(
            Account.id.in_(other_accounts)
        ):
            acc_to_cust[aid] = cid

    cust_agg: dict[int, _Agg] = {}
    merch_agg: dict[int, _Agg] = {}

    for t in txns:
        # Customer <-> customer transfers/wires.
        if t.merchant_id is None:
            if t.sender_account_id in acc_ids and t.receiver_account_id in acc_ids:
                continue  # internal (own account to own account)
            if t.receiver_account_id in acc_ids and t.sender_account_id in acc_to_cust:
                cid = acc_to_cust[t.sender_account_id]
                a = cust_agg.setdefault(cid, _Agg())
                a.inbound += t.amount
            elif t.sender_account_id in acc_ids and t.receiver_account_id in acc_to_cust:
                cid = acc_to_cust[t.receiver_account_id]
                a = cust_agg.setdefault(cid, _Agg())
                a.outbound += t.amount
            else:
                continue
            a.count += 1
            a.suspicious = a.suspicious or t.is_flagged
            a.txn_ids.append(t.id)
        # Subject -> merchant payments.
        elif t.sender_account_id in acc_ids:
            a = merch_agg.setdefault(t.merchant_id, _Agg(kind="merchant"))
            a.outbound += t.amount
            a.count += 1
            a.suspicious = a.suspicious or t.is_flagged
            a.txn_ids.append(t.id)

    # Enrich counterparty labels/risk.
    if cust_agg:
        for c in db.query(Customer).filter(Customer.id.in_(cust_agg.keys())):
            cust_agg[c.id].label = c.full_name
            cust_agg[c.id].risk_level = c.risk_level

    # Keep the top merchants by volume.
    top_merch = sorted(merch_agg.items(), key=lambda kv: kv[1].total, reverse=True)[
        :MAX_MERCHANTS
    ]
    top_merch_ids = {mid for mid, _ in top_merch}
    if top_merch_ids:
        for m in db.query(Merchant).filter(Merchant.id.in_(top_merch_ids)):
            agg = merch_agg[m.id]
            agg.label = m.name
            agg.is_high_risk = m.is_high_risk or (
                m.category in HIGH_RISK_MERCHANT_CATS
            )

    # --- Assemble nodes ---
    nodes: list[GraphNode] = [
        GraphNode(
            id=f"c{subject.id}",
            kind="customer",
            label=subject.full_name,
            sublabel=subject.occupation,
            risk_level=subject.risk_level,
            is_subject=True,
            total_amount=sum(a.total for a in cust_agg.values())
            + sum(a.total for a in merch_agg.values()),
        )
    ]
    for cid, a in cust_agg.items():
        nodes.append(
            GraphNode(
                id=f"c{cid}",
                kind="customer",
                label=a.label or f"Customer {cid}",
                risk_level=a.risk_level,
                total_amount=round(a.total, 2),
            )
        )
    for mid, a in top_merch:
        nodes.append(
            GraphNode(
                id=f"m{mid}",
                kind="merchant",
                label=a.label or f"Merchant {mid}",
                sublabel="merchant",
                is_high_risk=a.is_high_risk,
                total_amount=round(a.total, 2),
            )
        )

    # --- Assemble edges ---
    edges: list[GraphEdge] = []
    for cid, a in cust_agg.items():
        # Orient the edge by dominant flow direction.
        if a.inbound >= a.outbound:
            source, target = f"c{cid}", f"c{subject.id}"
        else:
            source, target = f"c{subject.id}", f"c{cid}"
        edges.append(
            GraphEdge(
                id=f"e-c{cid}",
                source=source,
                target=target,
                amount=round(a.total, 2),
                count=a.count,
                suspicious=a.suspicious,
                transaction_ids=a.txn_ids,
            )
        )
    for mid, a in top_merch:
        edges.append(
            GraphEdge(
                id=f"e-m{mid}",
                source=f"c{subject.id}",
                target=f"m{mid}",
                amount=round(a.total, 2),
                count=a.count,
                suspicious=a.suspicious,
                transaction_ids=a.txn_ids,
            )
        )

    return GraphData(nodes=nodes, edges=edges)
