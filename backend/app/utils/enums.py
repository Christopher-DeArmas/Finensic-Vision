"""Shared enumerations used across models, schemas, and the rule engine.

Using ``str, Enum`` makes values JSON-serializable and readable in the DB.
"""

from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def from_score(cls, score: int) -> "RiskLevel":
        """Map a 0-100 score to a risk band (critical requires 80+)."""
        if score < 40:
            return cls.LOW
        if score < 60:
            return cls.MEDIUM
        if score < 80:
            return cls.HIGH
        return cls.CRITICAL


class KycStatus(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    REJECTED = "rejected"


class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    WIRE = "wire"


class PaymentMethod(str, Enum):
    ACH = "ach"
    WIRE = "wire"
    CARD = "card"
    CASH = "cash"
    CRYPTO = "crypto"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class CaseStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CLOSED = "closed"
    FILED_SAR = "filed_sar"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScenarioTag(str, Enum):
    """Labels for intentionally planted laundering scenarios."""

    STRUCTURING = "structuring"
    RAPID_MOVEMENT = "rapid_movement"
    CIRCULAR_RING = "circular_ring"
    DORMANT_AWAKENING = "dormant_awakening"
    VELOCITY_BURST = "velocity_burst"
    GEO_ANOMALY = "geo_anomaly"
    MONEY_MULE = "money_mule"
    CRYPTO_LAYERING = "crypto_layering"
    ACCOUNT_EXPLOSION = "account_explosion"


class RelationshipType(str, Enum):
    TRANSFER = "transfer"
    FAMILY = "family"
    BUSINESS = "business"
    RING = "ring"
