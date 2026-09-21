# Sentinel Anti-Cheat

Sentinel is a chess integrity platform for arbiters and federations. It analyzes games for statistical signs of engine assistance and produces explainable, non-accusatory risk findings for human review — it never issues a cheating verdict itself.

The system implements a Regan-style statistical baseline (move-by-move engine agreement and centipawn loss compared against a player's own history) combined with additional behavioral, timing, and operational signal layers, fused into a single risk tier with a plain-language explanation for arbiters.

## Design principles

- **No automated verdicts.** Output is always a risk tier (`LOW` / `MODERATE` / `ELEVATED` / `HIGH_STATISTICAL_ANOMALY`) with supporting evidence, never an accusation. High-risk outcomes require mandatory human review.
- **Explainable by layer.** Every signal that contributes to a score reports its own reasons, so an arbiter can see *why*, not just *what*.
- **Conservative by default.** New players get a cold-start confidence downgrade rather than an inflated risk score, and official/high-stakes analysis rejects games missing clock data (`%clk`) rather than guessing.
- **Auditable.** Every analysis is written to an immutable, hash-chained audit trail.

## Project layout

- `backend/` — FastAPI service: the five-layer signal engine, Stockfish-backed PGN analysis, and audit logging
- `web/` — Next.js operator dashboard shell for arbiters
- `supabase/schema.sql` — Postgres schema for players, events, games, move features, and analyses
- `ROADMAP.md` — detailed implementation status and handover notes
- `docs/internal/` — working notes and build specs (development history, not user-facing documentation)

## Implemented now

- Five independent signal layers with explainable per-layer reasons
- Weighted fusion with severe-signal override (prevents rigid 3-of-5 blind spots)
- Cold-start confidence downgrade (detection remains active for new players)
- High-stakes clock policy: missing `%clk` is rejected for official analysis
- Analysis-window filtering hooks (opening/tablebase/forced move exclusions)
- Stockfish-backed PGN analysis endpoint (`/v1/analyze-pgn`) with MultiPV and move-level feature extraction
- SQLite audit trail + Supabase persistence (`players/events/analyses`)

## Still required for full production parity with the specification

- Engine-performance tuning and calibration against benchmark datasets
- Polyglot/Syzygy production data provisioning and quality checks
- Trained XGBoost + IsolationForest calibration pipeline and model versioning
- Supabase auth/row-level security and API persistence wiring
- Full investigation workflow UI (case management, SHAP charting, arbiter review actions)

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

- Copy `backend/.env.example` to `backend/.env`
- Set `STOCKFISH_PATH` to your Stockfish executable
- Fill `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- Fill `REDIS_URL`, `REDIS_PASSWORD`, `REDIS_PREFIX`

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

- `GET /health`
- `POST /v1/analyze`
- `POST /v1/analyze-pgn` — Stockfish-backed; requires `STOCKFISH_PATH`

Persistence:

- `/v1/analyze` writes `analyses` + identity upserts
- `/v1/analyze-pgn` writes `analyses`, `games`, `move_features`, `engine_evals`

The analyze response returns:

- `risk_tier` (`LOW`, `MODERATE`, `ELEVATED`, `HIGH_STATISTICAL_ANOMALY`)
- `confidence`
- `analyzed_move_count`
- `weighted_risk_score`
- `signals[]` with score/threshold/reasons per layer
- immutable `audit_id`
