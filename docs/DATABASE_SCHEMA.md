# Sentinel AML — Database Schema

SQLite database accessed through SQLAlchemy. The schema is normalized: entities
(customers, accounts, merchants) are separated from events (transactions) and
from investigation artifacts (alerts, cases, risk_scores, sar_reports). All
monetary values are stored in the transaction's `currency`; amounts are `REAL`
(sufficient for a demo — a production system would use integer minor units).

## Entity-relationship overview

```
customers ──1:N──▶ accounts ──1:N──▶ transactions ◀──N:1── merchants
    │                                     │
    │                                     └── sender_account_id / receiver_account_id
    │
    ├──1:N──▶ risk_scores
    ├──1:N──▶ alerts ──1:N──▶ cases ──1:1──▶ sar_reports
    └──N:N──▶ relationships (customer ↔ customer)

alerts ──N:N──▶ transactions   (alert_transactions join table)
cases  ──N:N──▶ transactions   (case_transactions join table)
```

## Tables

### `customers`
The account holders under (potential) investigation.

| Column                    | Type      | Notes                                            |
| ------------------------- | --------- | ------------------------------------------------ |
| `id`                      | INTEGER PK|                                                  |
| `full_name`               | TEXT      |                                                  |
| `occupation`              | TEXT      |                                                  |
| `country`                 | TEXT      | ISO-ish country name                             |
| `city`                    | TEXT      |                                                  |
| `annual_income`           | REAL      | Declared annual income (USD)                     |
| `expected_monthly_income` | REAL      | KYC expectation                                  |
| `expected_monthly_spend`  | REAL      | KYC expectation                                  |
| `risk_level`              | TEXT      | `low` / `medium` / `high` / `critical`           |
| `kyc_status`              | TEXT      | `verified` / `pending` / `rejected`              |
| `is_high_risk_jurisdiction` | BOOLEAN |                                                  |
| `date_opened`             | DATETIME  |                                                  |
| `scenario_tag`            | TEXT NULL | Marks planted scenarios (e.g. `structuring`)     |
| `created_at`              | DATETIME  |                                                  |

Indexes: `country`, `risk_level`, `scenario_tag`.

### `accounts`
Each customer has a checking + savings account, and optionally a business one.

| Column           | Type       | Notes                                    |
| ---------------- | ---------- | ---------------------------------------- |
| `id`             | INTEGER PK |                                          |
| `customer_id`    | INTEGER FK | → `customers.id`                         |
| `account_number` | TEXT UNIQUE|                                          |
| `account_type`   | TEXT       | `checking` / `savings` / `business`      |
| `currency`       | TEXT       | Default `USD`                            |
| `balance`        | REAL       | Current balance                          |
| `opened_at`      | DATETIME   |                                          |
| `last_activity_at` | DATETIME NULL | Used by dormant-account rule          |
| `is_dormant`     | BOOLEAN    | Derived flag                             |
| `created_at`     | DATETIME   |                                          |

Indexes: `customer_id`, `account_type`.

### `merchants`
Counterparties for card/merchant transactions.

| Column     | Type       | Notes                                            |
| ---------- | ---------- | ------------------------------------------------ |
| `id`       | INTEGER PK |                                                  |
| `name`     | TEXT       |                                                  |
| `category` | TEXT       | e.g. `crypto_exchange`, `grocery`, `casino`      |
| `country`  | TEXT       |                                                  |
| `city`     | TEXT       |                                                  |
| `mcc`      | TEXT       | Merchant category code                           |
| `is_high_risk` | BOOLEAN|                                                  |
| `created_at` | DATETIME |                                                  |

Index: `category`.

### `transactions`
The core event table (thousands of rows). A transaction may be account→account
(transfer/deposit) or account→merchant (payment/withdrawal).

| Column               | Type       | Notes                                                    |
| -------------------- | ---------- | -------------------------------------------------------- |
| `id`                 | INTEGER PK |                                                          |
| `external_id`        | TEXT UNIQUE| Public reference (e.g. `TXN-0000123`)                    |
| `timestamp`          | DATETIME   | Indexed                                                  |
| `sender_account_id`  | INTEGER FK NULL | → `accounts.id`                                     |
| `receiver_account_id`| INTEGER FK NULL | → `accounts.id`                                     |
| `merchant_id`        | INTEGER FK NULL | → `merchants.id`                                    |
| `transaction_type`   | TEXT       | `deposit` / `withdrawal` / `transfer` / `payment` / `wire` |
| `payment_method`     | TEXT       | `ach` / `wire` / `card` / `cash` / `crypto`             |
| `merchant_category`  | TEXT NULL  | Denormalized snapshot for fast filtering                 |
| `amount`             | REAL       |                                                          |
| `currency`           | TEXT       |                                                          |
| `country`            | TEXT       | Where the transaction occurred                           |
| `city`               | TEXT       |                                                          |
| `latitude`           | REAL       | For geographic-anomaly rule + heatmap                    |
| `longitude`          | REAL       |                                                          |
| `device_id`          | TEXT       |                                                          |
| `ip_address`         | TEXT       |                                                          |
| `is_flagged`         | BOOLEAN    | Set by rule engine                                       |
| `created_at`         | DATETIME   |                                                          |

Indexes: `timestamp`, `sender_account_id`, `receiver_account_id`,
`merchant_id`, `transaction_type`, `country`.

### `risk_scores`
Point-in-time normalized (0–100) score per customer, with the contributing
rule breakdown stored as JSON for full explainability.

| Column         | Type       | Notes                                        |
| -------------- | ---------- | -------------------------------------------- |
| `id`           | INTEGER PK |                                              |
| `customer_id`  | INTEGER FK | → `customers.id`                             |
| `score`        | INTEGER    | 0–100                                         |
| `risk_level`   | TEXT       | Derived band                                 |
| `breakdown`    | JSON       | `[{rule, points, reason, severity}, …]`      |
| `computed_at`  | DATETIME   |                                              |

### `alerts`
Raised when a customer's score crosses the alert threshold.

| Column         | Type       | Notes                                        |
| -------------- | ---------- | -------------------------------------------- |
| `id`           | INTEGER PK |                                              |
| `customer_id`  | INTEGER FK | → `customers.id`                             |
| `title`        | TEXT       |                                              |
| `description`  | TEXT       |                                              |
| `severity`     | TEXT       | `low` / `medium` / `high` / `critical`       |
| `score`        | INTEGER    | Score at time of alert                        |
| `triggered_rules` | JSON    | List of rule codes/names                     |
| `status`       | TEXT       | `open` / `in_review` / `dismissed` / `escalated` |
| `created_at`   | DATETIME   |                                              |

Linked to transactions via `alert_transactions` join table.

### `cases`
An investigation opened from an alert.

| Column         | Type       | Notes                                        |
| -------------- | ---------- | -------------------------------------------- |
| `id`           | INTEGER PK |                                              |
| `case_number`  | TEXT UNIQUE| e.g. `CASE-2026-0007`                         |
| `customer_id`  | INTEGER FK | → `customers.id`                             |
| `alert_id`     | INTEGER FK NULL | → `alerts.id`                           |
| `title`        | TEXT       |                                              |
| `status`       | TEXT       | `open` / `investigating` / `closed` / `filed_sar` |
| `priority`     | TEXT       | `low` / `medium` / `high` / `critical`       |
| `ai_summary`   | JSON NULL  | Cached AI investigation report               |
| `analyst_notes`| TEXT NULL  |                                              |
| `opened_at`    | DATETIME   |                                              |
| `closed_at`    | DATETIME NULL |                                           |

Linked to transactions via `case_transactions` join table.

### `sar_reports`
A generated Suspicious Activity Report (1:1 with a case).

| Column          | Type       | Notes                                       |
| --------------- | ---------- | ------------------------------------------- |
| `id`            | INTEGER PK |                                             |
| `case_id`       | INTEGER FK | → `cases.id`                                |
| `reference`     | TEXT UNIQUE| e.g. `SAR-2026-0007`                         |
| `summary`       | TEXT       |                                             |
| `customer_section` | TEXT    |                                             |
| `reason`        | TEXT       |                                             |
| `evidence`      | JSON       | Structured evidence list                     |
| `timeline`      | JSON       | Ordered timeline events                      |
| `recommendation`| TEXT       |                                             |
| `analyst_notes` | TEXT NULL  |                                             |
| `generated_at`  | DATETIME   |                                             |

### `relationships`
Customer-to-customer links that power the graph and circular-transfer /
multiple-source detection.

| Column            | Type       | Notes                                            |
| ----------------- | ---------- | ------------------------------------------------ |
| `id`              | INTEGER PK |                                                  |
| `source_customer_id` | INTEGER FK | → `customers.id`                             |
| `target_customer_id` | INTEGER FK | → `customers.id`                             |
| `relationship_type` | TEXT     | `transfer` / `family` / `business` / `ring`      |
| `strength`        | REAL       | Aggregate transfer weight                         |
| `created_at`      | DATETIME   |                                                  |

### Join tables

- `alert_transactions(alert_id, transaction_id)`
- `case_transactions(case_id, transaction_id)`

## Planted scenarios (`customers.scenario_tag`)

To guarantee investigations during the demo, the generator plants labeled
customers whose transactions are engineered to trip specific rules:

| `scenario_tag`       | Behavior planted                                          |
| -------------------- | -------------------------------------------------------- |
| `structuring`        | Repeated deposits of \$9,000–\$9,900 (just under \$10k). |
| `rapid_movement`     | Large inbound funds withdrawn/transferred within 2 hours. |
| `circular_ring`      | A→B→C→A transfer loop among 3–4 customers.                |
| `dormant_awakening`  | 6+ months inactive, then a sudden large inbound wire.     |
| `velocity_burst`     | Many transfers within minutes.                            |
| `geo_anomaly`        | Transactions from impossible location pairs (e.g. FL→Tokyo in 15 min). |
| `money_mule`         | 20+ unrelated senders funneling into one account.         |
| `crypto_layering`    | Rapid layering through crypto-exchange merchants + high-risk jurisdictions. |
| `account_explosion`  | Newly opened account receiving unusually large volume.    |

Normal customers have `scenario_tag = NULL`.
