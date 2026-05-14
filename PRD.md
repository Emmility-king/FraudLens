# Fine-Guard AI — Product Requirements Document

This document is the authoritative product specification for **Fine-Guard AI**: a professional-grade web platform that identifies subtle, complex fraud patterns in large financial datasets using deep learning, with explainable insights and an investigator-focused UI.

---

## 1. Product Overview

Fine-Guard AI is a high-performance web application that uses deep learning to detect **fine-grained** fraud—patterns that often bypass traditional rule-based systems. It gives financial investigators a real-time (or near-real-time) dashboard and **explainable** evidence for suspicious transactions.

**Mission:** Ingest large-scale transaction data, run it through a deep learning model tuned for subtle anomalies, and present results in a high-trust, data-dense dashboard.

---

## 2. Target Audience

- **Financial risk analysts** — monitor high volumes of transactions.
- **Fraud investigators** — need drill-down detail and reasoning (XAI) behind alerts.
- **Compliance officers** — need defensible monitoring aligned with regulatory expectations.

---

## 3. Core Objectives

- **Subtle detection** — surface low-signal or structurally complex fraud that rule engines miss.
- **Explainability** — never “black box only”; show which factors drove the risk score.
- **Scalability** — handle large datasets with an asynchronous, modern stack.

---

## 4. Functional Requirements

### 4.1 AI Engine & Modeling

- **Architecture:** Implement an **autoencoder** (unsupervised anomaly detection via reconstruction error) and/or a **graph neural network (GNN)** for fraud-ring / relational patterns.
- **Imbalance handling:** Use techniques such as **SMOTE** where labels exist or for hybrid/supervised heads so rare fraud classes are learnable.
- **Inference:** Backend serves the model with **sub-second latency** targets for interactive and monitoring use cases.

### 4.2 Web Interface (UI/UX)

- **Real-time dashboard** — KPI cards (e.g. flagged volume, risk distribution), dense but readable layout (“Bloomberg-style” information density without clutter).
- **Batch upload** — drag-and-drop **CSV** and **Excel** for bulk historical analysis.
- **Investigation module** — per-transaction drill-down with color-coded risk (green / yellow / red) and a **risk score** gauge.
- **Trust & transparency** — professional palette: deep blues, slate, action red for alerts; optional dark / high-contrast enterprise fintech theme.
- **Micro-interactions** — clear loading and processing states when AI work is in flight.

### 4.3 Explainable AI (XAI)

- **Feature attribution** — charts or structured lists (e.g. SHAP- or LIME-style) showing which variables (location jump, velocity, amount vs. history, etc.) contributed most to the score.

---

## 5. Technical Specifications

| Component | Technology |
|-----------|------------|
| **Runtime** | Python 3.12+ |
| **Backend API** | FastAPI (async, high performance) |
| **Deep learning** | PyTorch *or* TensorFlow / Keras — autoencoder and/or GNN for anomaly detection |
| **Frontend** | React (Vite) + TypeScript |
| **Styling** | Tailwind CSS |
| **Visualization** | Recharts or D3.js (transaction mapping, risk trends, gauges) |
| **Database** | **SQLite** for this school deployment (transaction logs and metadata); PostgreSQL remains a production-grade upgrade path |
| **Preprocessing** | Pandas, NumPy |

### School / coursework deployment

The reference architecture allows **PostgreSQL** at scale; **this repository targets SQLite** so the app runs on a single machine with no separate database server. SQLAlchemy models stay portable so swapping the connection string to Postgres later is straightforward.


## 6. System Architecture & Data Flow

1. **Ingestion** — Stream via API and/or batch file upload (CSV / Excel).
2. **Preprocessing** — Backend validates, cleans, and engineers features (e.g. inter-transaction time deltas, velocity, aggregates).
3. **Analysis** — Model outputs **reconstruction error** (autoencoder) and/or **graph-based anomaly score** (GNN).

   For an autoencoder, a common fraud signal is high **mean squared error (MSE)** between input \(x\) and reconstruction \(x'\):

   \[
   L(x, x') = \frac{1}{n} \sum_{i=1}^{n} (x_i - x'_i)^2
   \]

   Elevated \(L\) suggests the transaction (or pattern) is poorly reconstructed by “normal” behavior—candidate fraud.

4. **Persistence** — Store transactions, scores, job status, and explanation artifacts in **SQLite** (file-based, suitable for coursework and demos).
5. **Visualization** — API feeds the React app: dashboard, tables, investigation view, XAI panels.

---

## 7. Core Features (Build Checklist)

1. **AI engine** — DL model for imbalanced / rare fraud; sequential or tabular transaction features as agreed in implementation.
2. **XAI** — UI shows *why* a case was flagged, not only *that* it was flagged.
3. **Real-time dashboard** — live or refreshable feed of flagged transactions with professional layout.
4. **Batch upload** — large-file upload path with progress and error reporting.
5. **Investigation view** — single-transaction page with risk gauge and evidence.

---

## 8. Development Standards

- Modular codebase; clear separation of API, data layer, training, and inference.
- **PEP 8** for Python; consistent TypeScript style on the frontend.
- Document public APIs and non-obvious model assumptions.
- Start from an agreed **folder structure** and evolve via PRs or milestones.

---

## 9. Roadmap & Success Metrics

### Phases

- **Phase 1 (MVP)** — FastAPI backend, baseline autoencoder (or agreed MVP model), React table/list of flagged transactions, basic scoring API.
- **Phase 2** — XAI surfaces in UI; batch upload end-to-end; richer charts.
- **Phase 3** — Live monitoring via **WebSockets** (or equivalent) for a continuous flag feed.

### Success metrics

- **Precision / recall** — strong fraud detection with controlled false positives (tune per deployment).
- **Investigator efficiency** — target **under ~2 minutes** to reach a confident triage decision for a typical case using dashboard + investigation + XAI.

---

## 10. Data & Testing Notes

- If no production dataset is available initially, the team may use **synthetic data** inspired by **PaySim**-style logic for development and demos.
- Model and API **versions** should be visible in the UI or `/meta` for auditability.

---

## 11. AI Assistant / Build “Master Prompt” (Reference)

When engaging coding assistants, the product intent can be summarized as:

**Role:** Senior full-stack developer and UI/UX designer for fintech + ML.

**Stack:** Python 3.12+, FastAPI, PyTorch or TensorFlow (autoencoder and/or GNN), React (Vite + TypeScript), Tailwind, Recharts or D3, **SQLite** (school project), Pandas/NumPy.

**First implementation ask (example):** Propose **repository folder structure** and the **recommended deep-learning architecture** for fine-grained detection (with rationale), then implement MVP in phases above.

---

*Document status: active. Changes to scope should update this file and be reflected in API and UI contracts. Step-by-step implementation: [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md).*
