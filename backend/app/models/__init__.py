"""ORM models package.

Importing this package registers every model on the shared ``Base.metadata``
so that ``create_all`` / ``drop_all`` can see them.
"""

from app.models.account import Account
from app.models.alert import Alert
from app.models.associations import alert_transactions, case_transactions
from app.models.case import Case
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.relationship import Relationship
from app.models.risk_score import RiskScore
from app.models.sar_report import SarReport
from app.models.transaction import Transaction

__all__ = [
    "Account",
    "Alert",
    "Case",
    "Customer",
    "Merchant",
    "Relationship",
    "RiskScore",
    "SarReport",
    "Transaction",
    "alert_transactions",
    "case_transactions",
]
