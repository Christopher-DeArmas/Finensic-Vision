# Sentinel AML — Architecture

## 1. Goals

Sentinel AML demonstrates the workflow of a bank AML department end to end:

1. **Ingest** a continuous stream of (synthetic) transactions.
2. **Detect** suspicious behavior using an explainable heuristic rule engine.
3. **Score** customers and raise **alerts** above a threshold.
4. **Investigate** via case files: profile, timeline, transaction graph,
   AI summary, and a generated SAR.

The design favors a clean, layered backend and a component-driven frontend so
that each hackathon stage slots into a well-defined seam.

## 2. High-level diagram

```
                        ┌────────────────────────────────────────────┐
                        │                 Frontend (React)            │
                        │  Dashboard · Investigation · Live Feed      │
                        │  React Flow · Recharts · Framer Motion      │
                        └───────────────┬───────────────┬────────────┘
                                REST     │               │  WebSocket
                                         ▼               ▼
                        ┌────────────────────────────────────────────┐
                        │                Backend (FastAPI)            │
                        │                                            │
                        │  api/  ──▶  services/  ──▶  repositories/  │
                        │              │      │            │         │
                        │           rules/   ai/       models/       │
                        │           graph/  streaming/               │
                        └───────────────┬────────────────────────────┘
                                         ▼
                        ┌────────────────────────────────────────────┐
                        │            SQLite (via SQLAlchemy)          │
                        └────────────────────────────────────────────┘
```

## 3. Backend layers (clean architecture)

The backend enforces a strict dependency direction: outer layers depend on
inner layers, never the reverse.

| Layer            | Package             | Responsibility                                                                 |
| ---------------- | ------------------- | ------------------------------------------------------------------------------ |
| **API**          | `app/api`           | HTTP/WebSocket controllers. Validate input (Pydantic), call services, shape responses. No business logic. |
| **Services**     | `app/services`      | Business logic and orchestration. Coordinate repositories, rules, graph, and AI. |
| **Rule engine**  | `app/rules`         | Pure, explainable AML heuristics. Each rule returns points, reason, severity. No I/O. |
| **Graph**        | `app/graph`         | Build the customer/account/merchant transaction network for visualization + path detection. |
| **AI**           | `app/ai`            | OpenAI prompt construction, investigation summaries, SAR generation, with an offline template fallback. |
| **Streaming**    | `app/streaming`     | Real-time transaction simulator + WebSocket connection manager.                |
| **Repositories** | `app/repositories`  | Data access. The only layer that touches the ORM session directly.             |
| **Models**       | `app/models`        | SQLAlchemy ORM entities (the normalized schema).                               |
| **Schemas**      | `app/schemas`       | Pydantic DTOs for API boundaries (decoupled from ORM models).                  |
| **Core**         | `app/core`          | Settings/config, DB engine + session, logging.                                 |
| **Data**         | `app/data`          | Synthetic data generation (Faker) including planted laundering scenarios.      |
| **Utils**        | `app/utils`         | Shared pure helpers (geo distance, currency, enums, time).                     |

### Dependency rule

```
api → services → { repositories → models, rules, graph, ai, streaming }
core, schemas, utils are cross-cutting and depend on nothing app-specific.
```

The rule engine is deliberately **pure** (no database access): a service loads
the relevant transactions/customer context and hands plain data structures to
the rules. This keeps rules unit-testable and explainable, and is the core of
the "explainable AI" story.

## 4. Frontend structure

| Folder                | Responsibility                                              |
| --------------------- | ---------------------------------------------------------- |
| `components/`         | Reusable presentational + composite UI (cards, tables, graph, charts). |
| `pages/`              | Route-level screens: Dashboard, Investigation, Cases, Search. |
| `hooks/`              | Data fetching + WebSocket hooks (`useLiveFeed`, `useCase`, …). |
| `services/`          | Typed API client + WebSocket client.                       |
| `types/`              | Shared TypeScript types mirroring backend schemas.         |
| `contexts/`           | Global state (live feed buffer, theme, filters).           |
| `lib/`                | Utilities (formatting, cn/tailwind helpers).               |

## 5. Real-time model

A background task in `app/streaming` emits 2–5 synthetic transactions per
second. Each transaction is (a) persisted, (b) evaluated by the rule engine,
and (c) broadcast to all connected WebSocket clients. When a customer's
cumulative risk crosses the alert threshold, an alert (and, on analyst action,
a case) is created. The frontend live feed animates incoming transactions and
flashes suspicious ones.

## 6. AI integration

`app/ai` builds a structured prompt from the customer profile, transactions,
triggered rules, and timeline, and requests a JSON investigation report from
OpenAI (executive summary, key findings, likely behaviors, risk assessment,
next steps). If `OPENAI_API_KEY` is absent, a deterministic template generator
produces equivalent, professional-sounding output so the demo never breaks.

## 7. Key design decisions

- **SQLite** for zero-setup speed; SQLAlchemy keeps a clean path to Postgres.
- **Explainable heuristics, not ML** — every risk point is attributable to a
  named rule with a human-readable reason, which is the product's core value.
- **Pure rule engine** — separated from persistence for testability and clear
  auditability.
- **Synthetic-first** — a reproducible seed (`SEED`) generates the same data
  and the same planted scenarios every run, making the demo predictable.
