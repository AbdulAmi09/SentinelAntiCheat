# Sentinel Anti-Cheat Roadmap and Handover

Last updated: 2026-03-13

## 1. Project Objective

Build a comprehensive chess anti-cheat platform combining:
- Regan-style statistical analysis and conservative federation policy thresholds
- Additional custom statistical, behavioral, historical, and operational signal layers
- Explainable risk outputs for arbiters/federations
- Strictly non-accusatory workflow (risk tiers only, mandatory human review for high-risk outcomes)

Core policy requirement:
- No direct cheating verdict output in system text
- High anomaly is always a statistical finding requiring human review

## 2. Current Implementation Status (Completed So Far)

### 2.1 Backend Core

Implemented:
- FastAPI service with endpoints:
  - `GET /health`
  - `POST /v1/analyze`
  - `POST /v1/analyze-pgn`
  - `POST /v1/tournament-summary` (new)
- Stockfish PGN ingestion pipeline with MultiPV support
- Analysis-window filtering:
  - opening-book exclusion hooks
  - tablebase (<=7 pieces) exclusion
  - forced move exclusion
  - single legal move exclusion
- Feature computation:
  - ACL, median CPL, CPL variance
  - engine match %, top-3 match %
  - complexity-adjusted metrics
  - critical moment accuracy
  - timing metrics (if clock available)
  - self-baseline z-scores (ACL/IPR/performance)
- Five-layer signal evaluation
- Weighted fusion with overrides
- Four-tier risk classification:
  - `LOW`, `MODERATE`, `ELEVATED`, `HIGH_STATISTICAL_ANOMALY`
- High-stakes clock-data enforcement
- System status endpoint `/v1/system-status` with diagnostic fields:
  - `lc0_ready`, `maia_models_detected`, `ml_models_loaded`, `analysis_pipeline_operational`
  - ML model load checks and warnings on startup

### 2.2 Policy and Phase 1 Statistical Additions

Implemented:
- `event_type` support in request schema (`online` default, `otb` supported)
- Federation-configurable thresholds with FIDE floor enforcement:
  - online floor `4.25`
  - OTB floor `5.00`
  - federation values can be raised but not lowered below floors (code enforces via `max`)
- Regan-compatible threshold usage in Layer 1 (event-type dependent)
- Natural-occurrence output:
  - standardized odds statement text
  - machine probability field (`natural_occurrence_probability`)
  - cap/floor display logic:
    - minimum shown `1 in 10`
    - maximum shown `1 in 1,000,000+`
    - one significant figure for `N`
    - if below threshold, output: `Within expected variation.`
- Initial Regan-style z-score calibration hook by rating band
- PEP scaffold metric (`pep_score`) based on equal positions
- Confidence intervals added for core metrics:
  - engine match
  - top-3 match
  - ACL
  - PEP
  - Regan Z (derived from ACL CI)
- Added Maia-aware per-move probability capture (lc0 + Maia weights) and Maia metrics in feature pipeline

### 2.3 Persistence and Schema

Implemented:
- Supabase schema hardening and additive migration-safe fields
- Missing `engine_evals` table added
- `events.event_type` added
- `analyses` enhanced with:
  - versioning fields
  - report fields
  - legal/human-review fields
  - `event_type`
  - `regan_threshold_used`
  - `natural_occurrence_statement`
  - `natural_occurrence_probability`
- SQLite audit logging maintained
- Supabase write mapping updated to include added metadata
- `move_features` now includes:
  - `engine_top1_match`, `engine_top3_match`, `maia_probability`

### 2.4 Web UI

Implemented:
- PGN console now captures `event_type` (`online` default)
- Result panel shows:
  - Regan Z/threshold
  - PEP score
  - natural-occurrence probability (scientific notation)
  - CI block for returned metrics
- Admin dashboard shows system status and model readiness indicators

### 2.5 Validation Performed

Completed:
- Backend tests: passing (`pytest -q`)
- Web production build: passing (`next build`)
- Backend tests still pass after ML pipeline updates (33 tests)

### 2.6 Phase 3 (Maia) + Evidence Report Additions

Implemented:
- Maia weights discovery now supports `MAIA_MODELS_DIR/maia-{elo}/model.pb`
- Maia policy integration using lc0 with `--verbose-move-stats`
- Per-move `maia_probability` stored and aggregated into Maia metrics
- Arbiter Evidence Report added to analysis response:
  - `engine_match_percentage`, `maia_agreement_percentage`
  - `engine_maia_disagreement`
  - `centipawn_loss_statistics`
  - `position_difficulty_metrics`
  - `analysis_layers`, `signals`
  - `player_anomaly_scores`, `player_anomaly_trend`, `player_anomaly_rolling_average`, `player_anomaly_spike_count`
  - `style_fingerprint` (deviation score + baseline games)

### 2.7 ML Fusion + Training Pipeline (In Progress)

Implemented:
- Expanded ML feature vector to include:
  - `engine_maia_disagreement`
  - difficulty metrics (`avg_engine_gap_cp`, `avg_position_complexity`, `avg_engine_rank`, `hard_best_move_rate`)
  - `rating_band_index`
  - `style_deviation_score`
- Added `style_fingerprint` module to compute baseline profile and deviation score
- Added difficulty features to PGN pipeline:
  - `engine_rank` and `legal_move_count` per move
- Training script added: `backend/scripts/train_models.py`
  - Streams Lichess games via API (no monthly dump)
  - Auto-discovery of players from Lichess leaderboards (blitz/rapid/classical)
  - Rating band assignment and quotas
  - Per-player game cap (default 12)
  - Writes dataset to `backend/data/raw/training_games.pgn`
  - Runs feature extraction, IsolationForest, pseudo-labels, XGBoost
  - Saves models to:
    - `backend/models/xgboost/v1.0/xgboost_model.json`
    - `backend/models/isolation_forest/v1.0/isolation_forest.pkl`
  - Calls `/v1/system-status` for verification

Dependencies added:
- `requests`, `zstandard` (for API fetch + streaming)

## 3. Critical Decisions from User (Must Not Change)

### 3.1 Threshold Policy

- Federation-configurable thresholds with FIDE floors:
  - OTB default/floor `5.00`
  - online default/floor `4.25`
- Federations may raise thresholds only
- System admin can adjust floors only if official FIDE standards change

### 3.2 Event Type

- `event_type` must exist in request schema
- default is `online`
- arbiters must explicitly choose `otb` for OTB events
- event type must be stored at event/tournament level and flow into analysis

### 3.3 Data Sourcing Priority

Use these sources in this order:
1. Lichess open DB + account status labels
2. Chess.com public APIs for additional labels
3. TWIC for clean OTB baseline
4. Regan public papers/presentations as prior calibration references

Class guidance:
- Negative class: 50,000+ non-banned games, stratified by 200-point rating bands
- Positive class: banned/closed accounts with >=20 games pre-ban

### 3.4 Odds Wording (Exact)

Use exactly:
- `The observed performance has an estimated probability of natural occurrence of approximately 1 in [N] games among players of similar rating and history.`

Rules:
- one significant figure for `N`
- minimum display `1 in 10`
- maximum display `1 in 1,000,000+`
- no percentages
- no impossible/certain language
- below threshold: `Within expected variation.`

## 4. What Is Still Left in Phase 1

Phase 1 is partially complete. Remaining high-priority items:

1. Real calibration dataset ingestion
- Build reliable local ETL pipeline for:
  - Lichess raw dumps and account metadata
  - Chess.com user/game archive pulls
  - TWIC PGN ingestion
- Produce normalized game-level calibration dataset

2. Generate production calibration profiles
- Replace scaffold defaults with measured rating-band stats from real datasets
- Maintain schema versioning for profile artifacts

3. Calibration QA
- Add checks:
  - min sample threshold per band
  - band continuity and smoothing checks
  - drift report vs previous profile

4. Tournament summary UI integration
- Backend endpoint exists
- Web UI still needs:
  - request wiring
  - per-game summary rendering
  - tournament-level CI display card

5. Phase 1 test expansion
- Add tests for:
  - event-type threshold routing
  - floor enforcement
  - odds text formatting boundaries
  - CI presence/shape
  - tournament summary consistency

## 5. Full Remaining Phases

## Phase 2: Advanced Move Quality and Context
- superhuman move rate
- rating-adjusted move probability
- opening familiarity index
- opponent strength correlation
- round-by-round anomaly clustering
- move-quality distribution uniformity tests
- explicit zero-blunder-in-complex-games rule

## Phase 3: Maia Stack
- Stockfish vs Maia divergence
- Maia humanness score
- personalized Maia model per player
- training/inference lifecycle and model version pinning

## Phase 4: Time and Clock Intelligence Completion
- time variance anomaly detection
- time clustering anomaly flag
- break timing correlation features (if available)
- robust null-safe clock handling and confidence effects

## Phase 5: Historical Modeling
- rolling 12-month weighting
- volatility score
- rating-band context and opponent-pool adjustments
- multi-tournament aggregation
- career trajectory growth curve

## Phase 6: ML Fusion Upgrade
- move from heuristic weighted fusion to:
  - calibrated XGBoost primary
  - Isolation Forest secondary
- calibrated probability outputs with monitoring/drift checks

## Phase 7: Explainability, Legal, Reporting
- SHAP values
- SHAP waterfall charts
- legal disclaimer enforcement in reports
- immutable append-only audit guarantees
- report lock/version workflow
- full dossier export (FIDE workflow format)

## Phase 8: Federation Ops, Live Mode, Security Integrations
- RBAC (arbiter/chief/federation/system roles)
- multi-federation tenancy controls
- complaint intake and sign-off workflows
- live tournament mode and per-move ticker
- physical security/event fusion (RF/metal/device incident correlation)
- optional camera/audio signals with strict no-raw-storage policy

## 6. Known Constraints and Risks

1. Current environment/network
- This completed work was built in a restricted environment; external data fetches were not executed here.
- Next session with network access should perform dataset pull/ETL.

2. Calibration state
- Current calibration values are scaffold defaults.
- Production use requires real profile build from data pipeline.

3. Governance and RBAC
- Policy logic exists, but full admin/federation permission model is not yet implemented.

4. ML training pipeline status
- Lichess API fetch can drop connections mid-stream; retry logic added but can still fail.
- Models not yet trained because API stream aborted mid-run; artifacts are still zero bytes.
- Requires `LICHESS_API_TOKEN` in `backend/.env` or environment.
- `/v1/system-status` check requires API running; otherwise it warns.

## 7. Files Added/Changed in This Workstream

Major backend:
- `backend/src/sentinel/config.py`
- `backend/src/sentinel/schemas.py`
- `backend/src/sentinel/main.py`
- `backend/src/sentinel/services/feature_pipeline.py`
- `backend/src/sentinel/services/signal_layers.py`
- `backend/src/sentinel/services/risk_engine.py`
- `backend/src/sentinel/services/policy.py` (new)
- `backend/src/sentinel/services/calibration.py` (new)
- `backend/src/sentinel/services/pgn_engine_pipeline.py`
- `backend/src/sentinel/repositories/supabase.py`
- `backend/src/sentinel/services/evidence_report.py`
- `backend/src/sentinel/services/maia_policy.py`
- `backend/src/sentinel/services/maia.py`
- `backend/src/sentinel/services/diagnostics.py`
- `backend/src/sentinel/services/ml_fusion.py`
- `backend/src/sentinel/services/style_fingerprint.py`
- `backend/scripts/train_models.py`

Calibration tooling:
- `backend/scripts/build_calibration_profile.py` (new)
- `backend/calibration/regan_calibration_profile.example.json` (new)

Schema:
- `supabase/schema.sql`

Web:
- `web/components/analysis-console.tsx`

Docs/env:
- `backend/README.md`
- `backend/.env.example`
- `backend/pyproject.toml`

## 8. Immediate Next Session Execution Plan

Step 1: Pre-flight checks
- Confirm network access and that `LICHESS_API_TOKEN` is available in `backend/.env`.
- Verify backend tests still pass (`python -m pytest -q`).
- Confirm model artifacts are non-empty after training:
  - `backend/models/xgboost/v1.0/xgboost_model.json`
  - `backend/models/isolation_forest/v1.0/isolation_forest.pkl`

Step 2: Run ML training pipeline (initial 3000 games)
- `python backend/scripts/train_models.py --max-games 3000`
- This fetches leaderboard seeds, fills rating bands, saves `training_games.pgn`.
- Expect 10–50MB dataset size; if API drops, re-run.
- Target rating-band quotas:
  - 800–1200: 1000 games
  - 1200–1800: 1000 games
  - 1800–2400: 800 games
  - 2400+: 200 games

Step 3: Post-train verification
- Confirm the training script prints evaluation summaries (anomaly score distribution, feature importance).
- Validate model load via:
  - `/v1/system-status`
- Verify `/v1/system-status` shows:
  - `ml_models_loaded: true`
  - `analysis_pipeline_operational: true`
- Increase training size gradually:
  - `--max-games 10000`, then `50000`, then `100000`.

Step 4: If Lichess API continues failing mid-run
- Reduce `--per-user-max` to 10
- Add more seed players or pause between requests
- Consider a smaller first pass (e.g., `--max-games 1000`) to validate pipeline.
- Re-run until rating-band quotas are met or near-met.

Step 5: After each training run
- Run `/v1/system-status` to confirm models load.
- Re-check the model files are not zero bytes.

## 9. Guardrails for Future Changes

- Do not remove currently working variation unless explicitly requested.
- Enhance additively where possible.
- Keep thresholds conservative and policy-compliant.
- Preserve non-accusatory language.
- Keep high-risk outputs human-review gated.

## 10. Notes for Next Session

- `backend/scripts/train_models.py` now loads `backend/.env` to read `LICHESS_API_TOKEN`.
- `train_models.py` uses Lichess leaderboards for seed discovery, then expands with opponents.
- Dataset quotas target rating bands; cap per-player games to avoid style bias.
- The training run was interrupted by connection errors; retry logic added.
- Models are still not trained because fetch failed mid-run; rerun is required.

## 11. Session End State (What To Do Next, In Order)

1. Start API server (if needed for `/v1/system-status`) and ensure internet access.
2. Run training once with `--max-games 3000`.
3. Confirm model artifacts exist and are non-empty at:
   - `backend/models/xgboost/v1.0/xgboost_model.json`
   - `backend/models/isolation_forest/v1.0/isolation_forest.pkl`
4. Call `/v1/system-status` and confirm:
   - `lc0_ready: true`
   - `maia_models_detected: true`
   - `ml_models_loaded: true`
   - `analysis_pipeline_operational: true`
5. If the API fetch fails, reduce `--max-games` or `--per-user-max` and re-run.
6. After the 3000-game run succeeds, scale to 10k → 50k → 100k.
