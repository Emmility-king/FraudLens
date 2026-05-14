# Fine-Guard AI — Implementation Plan (Backend & Frontend)

This document is the **step-by-step build guide** for the project. It complements the high-level [PROJECT_PLAN.md](./PROJECT_PLAN.md) and requirements in [PRD.md](./PRD.md). Follow backend and frontend tracks in the **recommended order** so integration points stay clear.

---

## How to use this document

1. Complete **Backend** steps **B1–B8** through at least the **stub scorer** before wiring most of the UI to live data.
2. Run **Frontend** steps **F1–F10** in parallel only where noted (e.g. F1–F3 anytime); **F4+** assume API contracts from the backend exist or are mocked.
3. Use **Integration checkpoints** to verify end-to-end behavior after each chunk.

**Stack reminder:** FastAPI + SQLAlchemy async + **SQLite** (`aiosqlite`), React (Vite + TypeScript) + Tailwind + Recharts in `frontend/`.

---

## Recommended global order

| Order | Track        | What |
|-------|--------------|------|
| 1     | Backend B1–B4 | Repo layout, config, DB, health/meta |
| 2     | Frontend F1–F3 | Env, API client shell, shared types |
| 3     | Backend B5–B7 | Upload, jobs, list flags (stub scores) |
| 4     | Frontend F4–F8 | Wire dashboard, table, upload, investigation |
| 5     | Backend B9–B12 | ML pipeline, real scores, XAI endpoint |
| 6     | Frontend F9–F10 | XAI charts, polish, optional WebSocket |

---

## Part A — Integration checkpoints

- **Checkpoint 1:** `GET /health` and `GET /api/v1/meta` return JSON; frontend can read `meta` from `VITE_API_BASE_URL`.
- **Checkpoint 2:** Upload CSV → `dataset_id` → `POST …/score` → `GET /jobs/{id}` → `succeeded`; `GET /api/v1/flags` returns rows the table can render.
- **Checkpoint 3:** `GET /api/v1/flags/{id}` returns detail + `xai_signals`; investigation view uses real payloads.
- **Checkpoint 4 (optional):** WebSocket or polling for “live” feed; demo script in README.

---

## Part B — Backend implementation steps

### B1 — Repository layout

- [ ] Create `backend/` (or `app/` at root—pick one convention and keep all FastAPI code under it).
- [ ] Structure suggested: `backend/app/main.py`, `backend/app/api/`, `backend/app/core/config.py`, `backend/app/db/`, `backend/app/models/`, `backend/app/schemas/`, `backend/app/services/`.
- [ ] Add `pyproject.toml` or keep `requirements.txt` at repo root; document `uvicorn` entrypoint (e.g. `uvicorn app.main:app --reload` from `backend/`).

### B2 — Configuration

- [ ] Load settings with `pydantic-settings` from `.env` (copy from [`.env.example`](./.env.example)).
- [ ] Expose `DATABASE_URL`, `API_V1_PREFIX`, optional `CORS_ORIGINS` for the Vite dev server (`http://localhost:5173`).

### B3 — Database engine and sessions

- [ ] Create async SQLAlchemy `engine` and `sessionmaker` for `sqlite+aiosqlite:///./data/fineguard.db` (ensure `data/` directory exists on startup or document manual creation).
- [ ] For SQLite + async: use `connect_args={"check_same_thread": False}` if needed; pool settings appropriate for file DB.

### B4 — Models and schema creation

- [ ] Define ORM models (minimal first pass):
  - **Dataset** — `id`, `filename`, `row_count`, `status`, `created_at`, optional `column_json`.
  - **Job** — `id`, `dataset_id`, `status` (`queued` / `running` / `succeeded` / `failed`), `error_message`, `created_at`, `finished_at`.
  - **Transaction** — `id`, `dataset_id`, raw or normalized fields you need for scoring (e.g. `occurred_at`, `amount`, `merchant`, `channel`, optional feature vector blob/JSON).
  - **Flag** — `transaction_id`, `risk_score`, `band`, optional `reconstruction_error`, `xai_json`.
- [ ] On startup (dev) or via Alembic later: `create_all` for MVP; document migration story for coursework.

### B5 — FastAPI application shell

- [ ] Instantiate `FastAPI(title="Fine-Guard AI", version="…")`.
- [ ] Mount API router under `API_V1_PREFIX` (e.g. `/api/v1`).
- [ ] Implement `GET /health` (always ok) and `GET /ready` (DB connection check).
- [ ] Implement `GET /api/v1/meta` — `api_version`, `model_version` (placeholder string until ML exists).

### B6 — CORS

- [ ] `CORSMiddleware` allowing origins from settings so the Vite app can call the API during development.

### B7 — Batch upload (CSV / XLSX)

- [ ] `POST /api/v1/datasets` — `multipart/form-data` with file; validate extension (`.csv`, `.xlsx`).
- [ ] Parse with **pandas** (`read_csv` / `read_excel` via openpyxl); enforce max row limit for school demo if desired.
- [ ] Persist **Dataset** row + bulk insert **Transaction** rows (chunked loop for large files).
- [ ] Return `dataset_id`, `row_count`, and optional list of parse warnings.

### B8 — Scoring job (stub first)

- [ ] `POST /api/v1/datasets/{dataset_id}/score` — create **Job** `queued`, return `job_id`.
- [ ] Run scoring in **background** (`BackgroundTasks` or `asyncio.create_task`): transition `running` → `succeeded` / `failed`.
- [ ] **Stub scorer:** assign `risk_score` (e.g. random or simple rule on amount) and write **Flag** rows; set `band` from thresholds.
- [ ] `GET /api/v1/jobs/{job_id}` — return status and error message if failed.

### B9 — Read APIs for the UI

- [ ] `GET /api/v1/flags` — pagination (`skip`/`limit` or `page`/`page_size`), optional filters (`min_risk`, `dataset_id`).
- [ ] `GET /api/v1/flags/stats` — aggregates for KPI cards (count by band, sum amounts for flagged, histogram buckets for chart).
- [ ] `GET /api/v1/flags/{transaction_id}` — single row + `xai_signals` (stub list OK at first).

### B10 — ML preprocessing

- [ ] Define a canonical **feature column set** agreed with the frontend display fields.
- [ ] Implement feature engineering module: time deltas, rolling velocity, amount vs. baseline, encodings; output a numeric tensor or vector per transaction.

### B11 — Autoencoder training and inference

- [ ] Training script (CLI under `backend/scripts/` or `ml/train_autoencoder.py`): load labeled or unlabeled data, fit autoencoder, save `model.pt` + `scaler.json` (or joblib) under `backend/artifacts/`.
- [ ] At API startup, **lazy-load** model; if missing, fall back to stub scorer and log warning.
- [ ] Replace stub: compute reconstruction MSE → map to `risk_score` with configurable threshold/percentile.

### B12 — Explainability endpoint

- [ ] Extend `GET /api/v1/flags/{id}` or add `GET /api/v1/flags/{id}/explain` — return structured `xai_signals` (e.g. per-feature squared error contribution or gradient-based attribution simplified for demo).
- [ ] Keep payload shape stable for the frontend types.

### B13 — Real-time feed (optional / stretch)

- [ ] `WebSocket /api/v1/stream/flags` or short polling contract; broadcast new flags after job batches (SQLite limits concurrent writers—keep scope modest for school).

### B14 — Quality and hand-in

- [ ] Add `pytest` tests for upload + job lifecycle + flags list (use temp SQLite file).
- [ ] Short **README** section: how to run backend + where DB file is created.

---

## Part C — Frontend implementation steps

### F1 — Environment variables

- [ ] Add `frontend/.env.example` with `VITE_API_BASE_URL=http://localhost:8000` (or your FastAPI port).
- [ ] Create `frontend/.env.local` (gitignored by Vite convention or document in root `.gitignore`) for local overrides.

### F2 — API client module

- [ ] Add `src/api/client.ts` — `fetch` wrapper with base URL from `import.meta.env.VITE_API_BASE_URL`, JSON helpers, typed errors.
- [ ] Centralize paths like `` `${base}/api/v1/flags` `` to avoid string drift.

### F3 — Shared TypeScript types

- [ ] Add `src/types/api.ts` mirroring backend Pydantic schemas: `FlagRow`, `FlagDetail`, `JobStatus`, `DatasetUploadResponse`, `StatsResponse`, `HistogramBin`.
- [ ] Keep types aligned when backend changes (single source of truth: OpenAPI codegen later optional).

### F4 — Replace mock dashboard KPIs

- [ ] On app load (or dedicated hook), `GET /api/v1/flags/stats` and bind to KPI cards; loading + error UI.

### F5 — Risk histogram

- [ ] Feed Recharts from API histogram endpoint or derive bins client-side from stats if backend sends raw distribution.

### F6 — Flags table

- [ ] Replace `mockFlags` with `GET /api/v1/flags` (pagination controls; `loading` / `error` / empty states).
- [ ] Sorting: client-side first; optional `sort` query param when backend supports it.

### F7 — Batch upload UI

- [ ] Wire drag-and-drop and file `<input>` to `POST /api/v1/datasets` using `FormData`.
- [ ] After success, show `dataset_id` and row count; trigger `POST …/score` and poll `GET /api/v1/jobs/{job_id}` until terminal state; toast or inline status (PRD micro-interactions).

### F8 — Investigation panel

- [ ] On row select, `GET /api/v1/flags/{transaction_id}`; populate gauge + detail fields from response.
- [ ] Map `band` + `risk_score` to existing color system.

### F9 — XAI presentation

- [ ] Render `xai_signals` as list or small bar chart (Recharts `BarChart` horizontal) from live data.
- [ ] Add short empty-state if backend returns no signals.

### F10 — Routing and polish (recommended)

- [ ] Add `react-router-dom`: routes `/` (dashboard), `/investigate/:id` (deep link from table).
- [ ] Optional: `useSWR` or TanStack Query for caching/refetch; debounce filters.
- [ ] Accessibility pass: table headers, focus states, `aria-live` for job status updates.

---

## Part D — API contract checklist (for both sides)

Use this as a shared checklist when implementing routes and the client.

| Method | Path | Purpose |
|--------|------|--------|
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | DB reachable |
| `GET` | `/api/v1/meta` | Versions |
| `POST` | `/api/v1/datasets` | Multipart file upload |
| `GET` | `/api/v1/datasets` | List datasets (optional MVP) |
| `POST` | `/api/v1/datasets/{id}/score` | Start scoring job |
| `GET` | `/api/v1/jobs/{job_id}` | Job status |
| `GET` | `/api/v1/flags` | Paginated flags |
| `GET` | `/api/v1/flags/stats` | KPI + histogram data |
| `GET` | `/api/v1/flags/{transaction_id}` | Investigation + XAI |
| `WS` | `/api/v1/stream/flags` | Optional live feed |

---

## Part E — What is already done (do not redo blindly)

- [x] Frontend scaffold: Vite + React + TypeScript + Tailwind + Recharts; dashboard **layout** with **mock data** ([`frontend/src/App.tsx`](./frontend/src/App.tsx)).
- [x] PRD, project phase plan, Python deps list, `.env.example` for SQLite.

Next implementation work: start at **B1** and **F1** in parallel, then converge at **Checkpoint 2**.

---

*Update this file when API paths or payloads change so coursework stays easy to follow.*
