# Fine-Guard AI — Project Plan (5 Phases)

This plan implements [PRD.md](./PRD.md): FastAPI + **SQLite** + PyTorch (autoencoder / later GNN) + React (Vite, TypeScript, Tailwind) + Recharts or D3.

**Granular build steps (backend + frontend):** see [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md).

---

## Local environment (Windows)

**Web UI:** the React app lives in [`frontend/`](./frontend/). From that folder run `npm install` (once), then `npm run dev` and open the URL Vite prints (usually `http://localhost:5173`).

1. From the repo root: `python -m venv .venv` (use **Python 3.12+** per PRD; 3.14 works if wheels exist for all packages).
2. Activate: `.\.venv\Scripts\Activate.ps1`  
   If scripts are blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
3. Upgrade installer: `python -m pip install --upgrade pip`
4. Install deps: `python -m pip install -r requirements.txt`  
   First install can take **10–25+ minutes** mainly because of **PyTorch** and scientific wheels.

Optional: copy [`.env.example`](./.env.example) to `.env` and set `DATABASE_URL` if you change the default SQLite path.

Deactivate when done: `deactivate`

---

## Phase 1 — Environment, layout, and API shell

**Goal:** Repeatable dev setup and a runnable backend skeleton contracts match the PRD.

- Use the **Local environment** section above (`.venv` at repo root).
- Define **monorepo folder layout** (e.g. `backend/`, `frontend/`, `ml/` or `backend/app/…`) without implementing all features yet.
- **FastAPI** app: `GET /health`, `GET /ready` (stub DB check), `GET /api/v1/meta` (API + placeholder model version).
- **Configuration:** `pydantic-settings`, `.env.example` (no secrets committed).
- **SQLite** via SQLAlchemy 2 async (`sqlite+aiosqlite:///…`); store the DB file under e.g. `./data/` (gitignored). Initial models for `datasets`, `jobs`, `transactions`, `flags` (minimal columns).
- **Deliverable:** `uvicorn` runs; DB migrates or creates tables; no ML required.

---

## Phase 2 — Ingestion, storage, and scoring jobs

**Goal:** Move real files into the system and track async work.

- **Batch upload API:** `multipart` CSV/XLSX, validation, column inference, row counts, error report for bad rows.
- **Persistence:** Store raw/normalized rows (or staged parquet paths if large); link to `dataset_id`.
- **Job model:** `POST …/score` creates a job; `GET /jobs/{id}` returns status (`queued` / `running` / `succeeded` / `failed`).
- **Background execution:** `asyncio` task queue or **ARQ/Celery** later; MVP can run in-process with clear seams for a worker.
- **Deliverable:** Upload a sample file → rows in DB → job completes (stub scorer acceptable: random or rule-based score) so the UI can be wired.

---

## Phase 3 — ML core: preprocessing, autoencoder, inference

**Goal:** PRD-aligned **fine-grained** anomaly signal (reconstruction MSE) on engineered features.

- **Feature engineering** module: time deltas, velocity, amount z-scores vs. window, categorical encodings as agreed in schema.
- **Training script** (CLI or notebook export): train **autoencoder** on “normal” or full data; save checkpoint + scaler metadata.
- **Imbalance:** If labels exist, **SMOTE** (or hybrid classifier head) documented and optional in pipeline.
- **Inference service:** load weights once at startup; batch tensor scoring with sub-second targets for moderate batch sizes.
- **Deliverable:** Real `risk_score` / reconstruction error written to `flags`; thresholds configurable.

---

## Phase 4 — Frontend: dashboard, table, investigation

**Goal:** Investigator-grade UI per PRD (dense, trustworthy, dark/enterprise theme).

- **`frontend/`** — Vite + React + TypeScript + Tailwind shell in place: KPI cards, Recharts histogram, flagged table, batch-upload drop zone (UI only until Phase 2), investigation panel with risk gauge + XAI placeholders. Add API client + `VITE_API_BASE_URL` when FastAPI routes exist.
- **Dashboard:** extend KPIs and charts as real data arrives.
- **Transaction table:** sortable, filterable, paginated flags feed.
- **Investigation page:** transaction detail, **risk gauge**, color bands (green / yellow / red).
- **Loading states** and transitions during uploads and scoring.
- **Deliverable:** End-to-end demo: upload → score → browse → drill-down (XAI can be placeholder copy until Phase 5).

---

## Phase 5 — XAI, live feed, and production hardening

**Goal:** Explainability, real-time feel, and operational quality.

- **XAI:** `GET …/explain` (or embedded signals) — feature contributions (gradient-based, SHAP, or LIME—pick one for MVP consistency); charts on investigation view.
- **Optional GNN** path: graph build from entities (user / merchant / device) and anomaly score v2 (can ship as experimental flag).
- **WebSocket** (or SSE): **live flag stream** for dashboard “ticker” / feed (Phase 3 in PRD terms).
- **Hardening:** rate limits on upload/explain, structured logging, basic auth or API keys for internal deploy, pytest on API + critical ML utils, README runbook.
- **Deliverable:** PRD Phase 2–3 capabilities met; system ready for pilot data and tuning.

---

## Dependency overview

```text
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5
  layout      data+jobs    ML+API      UI        XAI+WS+ops
```

Phases **2** and **3** can overlap slightly (stub scorer first, then swap in real model) as long as job APIs stay stable for the UI.

---

*Align changes with [PRD.md](./PRD.md).*
