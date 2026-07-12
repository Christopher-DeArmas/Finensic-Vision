# Finensic Vision — Sentinel AML

**Authors:** Christopher De Armas · Justin Qiu

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

## Quick start (backend)

```bash
cd backend

# 1. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env             # then edit as needed

# 4. Seed synthetic data AND run the AML engine (one command)
python -m scripts.reset_demo

# 5. Run the API
uvicorn app.main:app --reload
```

Then open the interactive API docs at **http://localhost:8000/docs** — a full
Swagger UI where you can call every endpoint (dashboard stats, customers,
transactions, alerts, and the alert-to-case workflow) against live data.

After seeding you will have a `sentinel.db` SQLite file containing 150
customers, their accounts, a merchant catalog, thousands of transactions, and
several intentionally planted laundering scenarios that will trigger the rule
engine during the demo.

> **Note:** SQLite can throw a disk-I/O error when the database file lives on an
> iCloud/Dropbox-synced or network folder. If that happens, point
> `DATABASE_URL` at a local path, e.g. `sqlite:////tmp/sentinel.db`.

### Frontend (dashboard)

With the backend running, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The Vite dev server proxies `/api` and `/ws`
to the backend, so the dashboard shows live KPIs, the risk distribution, a
fraud heatmap, top-risk customers, recent alerts, and a real-time transaction
feed (suspicious transactions flash red). Black & gold theme, dark mode.

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
