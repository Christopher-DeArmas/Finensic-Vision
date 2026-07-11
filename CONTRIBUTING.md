# Contributing to Finensic Vision (Sentinel AML)

This project is built by a small team during a hackathon. To keep the code
reviewable and avoid stepping on each other, we use a simple **branch → pull
request → review → merge** workflow. All examples below work with GitHub
Desktop (GUI) or the terminal.

---

## Golden rules

1. **Never commit straight to `main`.** `main` should always be runnable/demo-ready.
2. **One branch per feature or fix.** Keep changes focused and small.
3. **Every change lands via a Pull Request (PR)** that the other person reviews.
4. **Never commit secrets or data.** `.env`, `*.db`, and `node_modules` are
   already git-ignored — keep it that way. Use `backend/.env.example` as the
   template for new settings.

---

## The workflow (GitHub Desktop)

1. **Sync first.** Open GitHub Desktop → make sure you're on `main` →
   click **Fetch/Pull origin** so you have the latest.
2. **Create a branch.** **Branch → New Branch…** Name it clearly, e.g.
   `feature/aml-rule-engine` or `fix/geo-anomaly-threshold`. Base it on `main`.
3. **Do the work.** Edit code.
4. **Commit.** Write a short, present-tense summary
   (e.g. `Add structuring rule to AML engine`). Commit to your branch.
5. **Publish the branch** (**Publish branch** button) to push it to GitHub.
6. **Open a Pull Request.** Click **Create Pull Request** — it opens github.com
   with your branch targeting `main`. Add a title and a short description of
   what changed and how to test it. Request the other person as a reviewer.
7. **Review.** The reviewer reads the diff on github.com, leaves comments, and
   approves (or requests changes).
8. **Merge.** Once approved, click **Merge pull request** on github.com, then
   **delete the branch**.
9. Everyone **pulls `main`** again before starting the next branch.

### Terminal equivalent

```bash
git checkout main && git pull
git checkout -b feature/aml-rule-engine
# ...make changes...
git add -A
git commit -m "Add structuring rule to AML engine"
git push -u origin feature/aml-rule-engine
# then open the PR from the link git prints, or with: gh pr create
```

---

## Branch naming

| Prefix      | Use for                                  | Example                        |
| ----------- | ---------------------------------------- | ------------------------------ |
| `feature/`  | New functionality                        | `feature/websocket-stream`     |
| `fix/`      | Bug fixes                                | `fix/sar-download-encoding`    |
| `chore/`    | Tooling, deps, docs, cleanup             | `chore/update-readme`          |

---

## Commit messages

Short, imperative, and specific:

- ✅ `Add circular-transfer detection rule`
- ✅ `Normalize risk score to 0–100`
- ❌ `updates` / `wip` / `fixed stuff`

---

## Suggested division of work (staged build)

The build order lives in [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).
A natural split for two people:

- **Person A (backend/AI):** rule engine, scoring, REST APIs, WebSocket stream,
  OpenAI summaries + SAR generation.
- **Person B (frontend/UX):** dashboard, investigation page, React Flow graph,
  timeline, live feed, animations/polish.

Coordinate on the API contract (the Pydantic schemas in `backend/app/schemas`
and the TypeScript types in `frontend/src/types`) so both sides line up.

---

## Running the project locally

See the [README](README.md) for backend setup. In short:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m scripts.seed_db
```

> **Databases are not committed.** After cloning, each person runs
> `python -m scripts.seed_db` to build their own local `sentinel.db`. Because
> generation uses a fixed `SEED`, you both get identical data.

> **Keep the repo off iCloud.** Clone it somewhere local like `~/Finensic Vision`
> or `~/dev/`, not inside `Documents`/`Desktop` (which sync to iCloud and can
> move the folder unexpectedly).
