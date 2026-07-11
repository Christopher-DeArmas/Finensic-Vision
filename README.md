# Finensic Vision — Sentinel AML

**AI-Powered Anti-Money-Laundering Investigation Platform**

Finensic Vision is a demonstration prototype that simulates the software an AML
(Anti-Money-Laundering) department inside a major bank would use. It streams
synthetic banking transactions in real time, runs them through an explainable
heuristic rule engine, opens investigation cases for suspicious customers, and
gives analysts a graph, timeline, AI-generated summaries, and downloadable
Suspicious Activity Reports (SARs).

> ⚠️ **This is NOT a production AML system.** It uses entirely synthetic data
> generated with [Faker](https://faker.readthedocs.io/) and is built to
> showcase AML investigation workflows, explainable AI, graph analysis, and
> real-time analytics for a hackathon.

---

## Tech stack

| Layer          | Technology                                                        |
| -------------- | ----------------------------------------------------------------- |
| Frontend       | React, TypeScript, Vite, TailwindCSS, shadcn/ui, React Flow, Recharts, Framer Motion |
| Backend        | FastAPI, Python 3.10+                                              |
| Database       | SQLite (via SQLAlchemy)                                            |
| Communication  | REST + WebSockets                                                  |
| AI             | OpenAI API (with offline template fallback)                       |
| Deployment     | Frontend → Vercel · Backend → Render                              |

---

## Repository layout

```
.
├── backend/                # FastAPI service (clean architecture)
│   ├── app/
│   │   ├── api/            # HTTP routes / controllers
│   │   ├── core/          # config, database session, logging
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── repositories/  # data-access layer
│   │   ├── services/      # business logic
│   │   ├── rules/         # AML heuristic rule engine
│   │   ├── streaming/     # WebSocket transaction simulator
│   │   ├── graph/         # transaction-graph construction
│   │   ├── ai/            # OpenAI summaries + SAR generation
│   │   ├── utils/         # shared helpers
│   │   └── data/          # synthetic data generator (Faker)
│   ├── scripts/           # seed_db.py and other CLI utilities
│   └── tests/
├── frontend/               # React + Vite app
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── IMPLEMENTATION_PLAN.md
├── CONTRIBUTING.md
└── README.md
```

---

## Quick start (backend — Stage 1)

```bash
cd backend

# 1. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env             # then edit as needed

# 4. Seed the database with synthetic data
python -m scripts.seed_db

# 5. (later stages) Run the API
uvicorn app.main:app --reload
```

After seeding you will have a `sentinel.db` SQLite file containing 150
customers, their accounts, a merchant catalog, thousands of transactions, and
several intentionally planted laundering scenarios that will trigger the rule
engine during the demo.

> **Note:** SQLite can throw a disk-I/O error when the database file lives on an
> iCloud/Dropbox-synced or network folder. If that happens, point
> `DATABASE_URL` at a local path, e.g. `sqlite:////tmp/sentinel.db`.

---

## Environment variables

See [`backend/.env.example`](backend/.env.example). Key values:

| Variable          | Purpose                                                       |
| ----------------- | ------------------------------------------------------------- |
| `DATABASE_URL`    | SQLAlchemy URL (defaults to local `sqlite:///./sentinel.db`)  |
| `OPENAI_API_KEY`  | Enables live AI summaries/SARs. If unset, a template fallback is used so the demo always works offline. |
| `OPENAI_MODEL`    | OpenAI chat model name (default `gpt-4o-mini`).               |
| `STREAM_MIN_TPS` / `STREAM_MAX_TPS` | Range of simulated transactions per second.  |
| `SEED`            | RNG seed for reproducible synthetic data.                     |

---

## Build stages

This project is built in the staged order below. **Stages 1–2 are complete.**

1. ✅ **Backend + database** — schema, models, synthetic data generation
2. ✅ AML rule engine + risk scoring
3. ⬜ REST APIs
4. ⬜ WebSocket transaction stream
5. ⬜ React dashboard
6. ⬜ Investigation page (React Flow graph + timeline)
7. ⬜ OpenAI summaries + SAR generation
8. ⬜ Polish: animations, loading states, error handling

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md) for detail, and
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the team workflow.
