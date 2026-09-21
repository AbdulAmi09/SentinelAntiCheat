# Sentinel Anti-Cheat

Sentinel is a chess integrity platform for arbiters and federations. It analyzes games for statistical signs of engine assistance and produces explainable, non-accusatory risk findings for human review — it never issues a cheating verdict itself.

The core is a Regan-style statistical baseline (move-by-move engine agreement and centipawn loss measured against a player's own history and rating), extended with six additional signal layers covering complexity, timing, historical, behavioral, online-behavioral, and environmental/identity patterns. All seven are fused into a single risk tier with a plain-language explanation, backed by a case-management and audit workflow built for arbiters rather than developers.

## Design principles

- **No automated verdicts.** Output is always a risk tier (`LOW` / `MODERATE` / `ELEVATED` / `HIGH_STATISTICAL_ANOMALY`) with supporting evidence, never an accusation. High-risk outcomes require mandatory human review, and every response carries a natural-occurrence probability statement plus a legal disclaimer rather than a conclusion.
- **Explainable by layer.** Each of the seven signal layers reports its own trigger conditions and reasons, so an arbiter can see *why*, not just *what*.
- **Conservative by default.** New players get a cold-start confidence downgrade rather than an inflated risk score, and official/high-stakes analysis rejects games missing clock data (`%clk`) rather than guessing.
- **Auditable.** Every analysis is written to a hash-chained, append-only audit log (each record links to the previous record's hash), with a report versioning/locking workflow so a finalized report can't be silently altered.

## Project layout

- `backend/` — FastAPI service: the seven-layer signal engine, Stockfish-backed PGN analysis, case management, OTB (over-the-board) incident intake, live-game monitoring, a partner API, and hash-chained audit logging
- `web/` — Next.js operator dashboard for arbiters
- `supabase/schema.sql` — Postgres schema for players, events, games, move features, and analyses
- `ROADMAP.md` — detailed implementation status and handover notes
- `docs/internal/` — working notes and build specs (development history, not user-facing documentation)

## What's implemented

**Analysis engine**
- Seven independent signal layers (move quality, complexity-adjusted accuracy, timing, historical baseline, behavioral, online-behavioral, environmental/identity), each with explainable per-layer reasons and thresholds
- Weighted fusion with a severe-signal override, so one strongly anomalous layer isn't diluted by four unremarkable ones
- Cold-start confidence downgrade for players without enough history
- High-stakes clock policy: official analysis rejects games missing `%clk` rather than silently skipping the timing layer
- Stockfish-backed PGN analysis (MultiPV, move-level feature extraction) plus Maia human-likeness comparison
- An ML fusion layer (XGBoost + Isolation Forest hooks) that falls back to the heuristic fusion above when no trained model is present — models are not yet trained (see below)

**Workflow & operations**
- Role-based access control (`arbiter`, `chief_arbiter`, `federation_admin`, `system_admin`)
- Case management: create/list/update cases, notes, evidence attachments, flags, and auto-flagging from analysis results
- Over-the-board incident intake, including camera-event and board-sensor-event ingestion
- Live-game monitoring (session-based, move-by-move risk updates)
- Report generation with versioning and locking, plus a partner API (API keys with rotation, webhooks, async job results) for federation integrations
- Tournament dashboards and per-player profile views

**Persistence & audit**
- Hash-chained SQLite audit trail (each entry references the previous entry's hash) with report version/lock state
- Supabase/Postgres persistence for players, events, games, move features, engine evaluations, and analyses

## What's not production-ready yet

- **ML models are untrained.** The XGBoost/Isolation Forest fusion path exists in code but ships with no trained weights; the system currently runs on the heuristic seven-layer fusion, not a calibrated ML model.
- **Engine/calibration tuning.** Stockfish depth/MultiPV settings and the Regan calibration profile need tuning and validation against benchmark datasets, not just default values.
- Polyglot/Syzygy production data provisioning and quality checks
- Supabase auth and row-level security wiring (persistence works; access control at the DB layer is not yet enforced)
- One backend test (`test_batch_analysis.py`) currently fails to collect — it references a PGN-normalization helper that was never implemented
- Full investigation-workflow UI polish (SHAP-style charting, more arbiter review affordances)

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
python -m uvicorn sentinel.main:app --reload --port 8000
```

If the editable install has not been run yet, use:

```bash
uvicorn --app-dir src sentinel.main:app --reload --port 8000
```

Backend environment:

- Copy `backend/.env.example` to `backend/.env` (never commit `.env` — it holds real credentials)
- Set `STOCKFISH_PATH` to your Stockfish executable
- Fill `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- Fill `REDIS_URL`, `REDIS_PASSWORD`, `REDIS_PREFIX`

Vendored engine/model binaries (Stockfish, lc0, Maia weights) and datasets are not committed to this repo — provision them locally per the paths above.

## Web setup

```bash
cd web
npm install
npm run dev
```

Web environment:

- Copy `web/.env.example` to `web/.env.local`
- Fill `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`

To analyze a game:

1. Open `http://localhost:3000`
2. Open the **PGN Analysis Console**
3. Paste a PGN into **PGN Text**
4. Submit to call `POST /v1/analyze-pgn`

## Database setup (Supabase/Postgres)

Run `supabase/schema.sql` against your database.

## API

The backend exposes roughly 40 endpoints under `/v1`, grouped as:

- **Analysis** — `POST /v1/analyze`, `POST /v1/analyze-pgn`, `POST /v1/tournament-summary`, `POST /v1/demo/analyze`
- **Reports & audit** — `GET/POST /v1/reports/{audit_id}`, lock/version endpoints, `GET /v1/audit/{audit_id}`, `POST /v1/reports/generate`
- **Case management** — `POST/GET /v1/cases`, notes, evidence, flags, auto-flags
- **Over-the-board** — incidents, camera events, board events
- **Live monitoring** — session create/get, move ingestion, live risk
- **Partner API** — analyze, job results, webhook registration, API key lifecycle
- **Dashboards** — `GET /v1/dashboard-feed`, `GET /v1/tournament-dashboard`, `GET /v1/players/{player_id}/profile`
- **System** — `GET /health`, `GET /v1/system-status`

A single game analysis (`POST /v1/analyze` or `/v1/analyze-pgn`) returns:

- `risk_tier` (`LOW`, `MODERATE`, `ELEVATED`, `HIGH_STATISTICAL_ANOMALY`)
- `confidence`
- `analyzed_move_count`
- `weighted_risk_score`
- `signals[]` with score/threshold/reasons per layer
- an immutable `audit_id`

## Security

See [SECURITY.md](SECURITY.md) for how to report a vulnerability.

## License

All rights reserved — see [LICENSE](LICENSE). This code is made available for evaluation, not for reuse or redistribution.
