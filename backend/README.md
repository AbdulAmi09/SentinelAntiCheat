# Sentinel Backend

FastAPI service for the Sentinel chess integrity platform.

## Install

```bash
pip install -e .
```

## Install (with dev tools)

```bash
pip install -e .[dev]
```

## Run

```bash
uvicorn sentinel.main:app --reload --port 8000
```

If you have not installed the package yet, run with src app-dir:

```bash
uvicorn --app-dir src sentinel.main:app --reload --port 8000
```

## Environment

Copy `.env.example` to `.env` and fill values:

- `STOCKFISH_PATH` (required for `/v1/analyze-pgn`)
- `POLYGLOT_BOOK_PATH` (optional, `.bin`)
- `SYZYGY_PATH` (optional, folder with `.rtbw/.rtbz`)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_SCHEMA` and `PERSISTENCE_FAIL_HARD`
- `REDIS_URL`, `REDIS_PASSWORD`, `REDIS_PREFIX`
- `MAIA_MODELS_DIR` (optional, directory containing `maia-1100.pb.gz`..`maia-1900.pb.gz`)
- `MAIA_LC0_PATH` (required if using Maia move probabilities)

## PGN + Engine endpoint

`POST /v1/analyze-pgn` requires `STOCKFISH_PATH`.

`high_stakes_event=true` requires clock tags (`%clk`) in PGN/move inputs.

Supabase persistence mapping:

- Always writes `analyses` (plus `players`/`events` upserts)
- For PGN endpoint also writes `games`, `move_features`, `engine_evals`
  - `move_features` includes `cp_loss`, `engine_top1_match`, `engine_top3_match`, `maia_probability`

Optional paths:

- `POLYGLOT_BOOK_PATH` for opening-book exclusion
- `SYZYGY_PATH` for tablebase-aware endgame filtering
- `CALIBRATION_PROFILE_PATH` for rating-band calibration JSON
- `MAIA_MODELS_DIR` + `MAIA_LC0_PATH` to compute per-move Maia probabilities

## Tournament summary endpoint

`POST /v1/tournament-summary` accepts the same body shape as `/v1/analyze` and returns:

- Tournament-level `ipr_estimate`, `pep_score`, `regan_z_score`, `regan_threshold`
- Confidence intervals for core metrics
- Per-game summary list with IPR/PEP/Regan outputs

## System status endpoint

`GET /v1/system-status` returns calibration, model, and engine readiness with warnings:

- Calibration profile source and QA summary
- Maia and ML fusion artifact status
- Stockfish, opening book, and tablebase path checks

Requires `X-Role: system_admin` (or any role that includes `system_status`).

## RBAC and federation scope (Phase 8 foundation)

All `/v1/*` endpoints support role and tenancy headers:

- `X-Role`: `arbiter`, `chief_arbiter`, `federation_admin`, `system_admin`
- `X-Federation-Id`: required for non-system roles when tenant enforcement is enabled

If you use event IDs in `{federation}::{event}` format, tenant checks will enforce federation match for non-system roles.

Environment toggles:

- `RBAC_ENABLED=true|false`
- `TENANT_ENFORCEMENT_ENABLED=true|false`

## Build a real calibration profile

Use the included script to build rating-band parameters from your prepared clean dataset:

```bash
python scripts/build_calibration_profile.py \
  --input calibration/clean_games.csv \
  --output calibration/regan_calibration_profile.json \
  --qa-report calibration/regan_calibration_profile.qa.json \
  --previous-profile calibration/regan_calibration_profile.previous.json \
  --profile-version 2026.03 \
  --source-dataset calibration/normalized_games.csv \
  --elo-column official_elo \
  --acl-column avg_acl \
  --label-column label \
  --clean-values clean,non_banned \
  --band-size 200 \
  --min-samples 100 \
  --fail-on-qa
```

Then set `CALIBRATION_PROFILE_PATH` in `.env` to the generated JSON path.

## Calibration dataset ETL (Lichess / Chess.com / TWIC)

Use `scripts/etl_calibration_dataset.py` to build normalized game-level rows.

Lichess NDJSON dump:

```bash
python scripts/etl_calibration_dataset.py lichess \
  --input data/lichess_games.ndjson.zst \
  --status-map data/lichess_status_map.csv \
  --output calibration/lichess_normalized.csv
```

Chess.com public archive pull:

```bash
python scripts/etl_calibration_dataset.py chesscom \
  --usernames-file data/chesscom_usernames.txt \
  --max-archives-per-user 12 \
  --output calibration/chesscom_normalized.csv
```

TWIC PGN ingestion:

```bash
python scripts/etl_calibration_dataset.py twic \
  --input data/twic.pgn \
  --output calibration/twic_normalized.csv
```

Merge all source-normalized files:

```bash
python scripts/etl_calibration_dataset.py merge \
  --inputs calibration/lichess_normalized.csv calibration/chesscom_normalized.csv calibration/twic_normalized.csv \
  --output calibration/normalized_games.csv
```
