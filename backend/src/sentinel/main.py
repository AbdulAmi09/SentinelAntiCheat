from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import secrets
from typing import Annotated, Union

from fastapi import FastAPI, HTTPException, Header, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sentinel.config import settings
from sentinel.repositories.audit import AuditRepository
from sentinel.repositories.investigation import InvestigationRepository
from sentinel.repositories.partner import PartnerRepository
from sentinel.repositories.supabase import SupabaseConfig, SupabaseRepository
from sentinel.schemas import (
    AnalyzePgnRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    CaseCreateRequest,
    CaseEvidenceCreateRequest,
    CaseFlagCreateRequest,
    CaseNoteCreateRequest,
    CaseStatusUpdateRequest,
    OTBIncidentCreateRequest,
    PartnerAnalyzeRequest,
    PartnerKeyCreateRequest,
    PartnerSessionCreateRequest,
    PartnerWebhookRegisterRequest,
    LiveMoveIngestRequest,
    LiveSessionCreateRequest,
    OTBCameraEventRequest,
    CameraServiceEventPayload,
    DGTBoardEventRequest,
    PlayerProfileResponse,
    ReportGenerateRequest,
    SystemStatusResponse,
    TournamentDashboardResponse,
    TournamentSummaryResponse,
    VisualsRequest,
)
from sentinel.services.authz import authorize_action, enforce_tenant_scope
from sentinel.services.diagnostics import startup_checks, system_status
from sentinel.services.ai_narrative import build_ai_narrative
from sentinel.services.evidence_report import build_evidence_report
from sentinel.services.explainability import build_explainability
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.live_monitoring import compute_live_risk
from sentinel.services.pgn_engine_pipeline import create_engine_context, game_to_inputs, parse_pgn_games
from sentinel.services.policy import natural_occurrence_probability, natural_occurrence_statement
from sentinel.services.crypto import hash_key
from sentinel.services.partner_jobs import PartnerJobWorker, generate_keypair, summarize_camera_events
from sentinel.services.rate_limit import build_rate_limiter
from sentinel.services.reporting import build_structured_report, report_to_csv, report_to_pdf
from sentinel.services.risk_engine import classify_with_meta
from sentinel.services.signal_layers import evaluate_all_layers
from sentinel.services.visuals import build_visuals_from_game

app = FastAPI(title="Sentinel Anti-Cheat API", version="0.1.0")
audit_repo = AuditRepository(settings.db_path)
investigation_repo = InvestigationRepository(settings.db_path)
partner_repo = PartnerRepository(settings.db_path)
partner_worker = PartnerJobWorker(partner_repo)
rate_limiter = build_rate_limiter()

class LiveConnectionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._sessions.setdefault(session_id, []).append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket) -> None:
        if session_id in self._sessions and websocket in self._sessions[session_id]:
            self._sessions[session_id].remove(websocket)
            if not self._sessions[session_id]:
                self._sessions.pop(session_id, None)

    async def broadcast(self, session_id: str, message: dict) -> None:
        for ws in list(self._sessions.get(session_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(session_id, ws)

live_connections = LiveConnectionManager()
supabase_repo: SupabaseRepository | None = None
if settings.supabase_url and settings.supabase_service_role_key:
    supabase_repo = SupabaseRepository(
        SupabaseConfig(
            url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            schema=settings.supabase_schema,
        )
    )
allowed_origins = [o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sdk_dir = (Path(__file__).resolve().parents[2] / "static" / "sdk")
if sdk_dir.exists():
    app.mount("/sdk", StaticFiles(directory=str(sdk_dir)), name="sdk")


@app.on_event("startup")
def _startup_checks() -> None:
    startup_checks()
    partner_worker.start()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _risk_rank(tier: str) -> int:
    order = {
        "HIGH_STATISTICAL_ANOMALY": 4,
        "ELEVATED": 3,
        "MODERATE": 2,
        "LOW": 1,
    }
    return order.get(tier, 0)


@app.get("/v1/dashboard-feed")
def dashboard_feed(
    limit: int = 200,
    event_id: str | None = None,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
    x_federation_id: Annotated[str | None, Header(alias="X-Federation-Id")] = None,
) -> dict:
    role = authorize_action(x_role, "dashboard_feed")
    enforce_tenant_scope(role, x_federation_id, event_id)
    rows = audit_repo.recent(limit=limit, event_id=event_id)
    game_map: dict[tuple[str, str], dict] = {}
    alerts: list[dict] = []

    for row in rows:
        req = row.get("request", {})
        resp = row.get("response", {})
        player_id = str(req.get("player_id") or resp.get("player_id") or "unknown")
        event_val = str(req.get("event_id") or resp.get("event_id") or "unknown")
        key = (event_val, player_id)
        weighted = float(resp.get("weighted_risk_score") or 0.0)
        risk_tier = str(resp.get("risk_tier") or "LOW")
        confidence = float(resp.get("confidence") or 0.0)
        created_at = str(row.get("created_at") or "")
        moves_count = int(resp.get("analyzed_move_count") or 0)
        req_elo = int(req.get("official_elo") or 0)

        # Keep newest row per player+event as game-card snapshot.
        existing = game_map.get(key)
        if existing is None:
            base = max(0.05, min(0.98, weighted))
            spark = [
                round(max(0.0, min(1.0, base * f)), 3)
                for f in (0.62, 0.67, 0.71, 0.76, 0.79, 0.84, 0.88, 0.93, 0.97, 1.0)
            ]
            game_map[key] = {
                "game_id": f"{event_val}:{player_id}",
                "event_id": event_val,
                "player_id": player_id,
                "official_elo": req_elo,
                "move_number": moves_count,
                "risk_tier": risk_tier,
                "confidence": confidence,
                "weighted_risk_score": weighted,
                "sparkline": spark,
                "audit_id": row["id"],
                "created_at": created_at,
            }

        for sig in resp.get("signals", []):
            if not sig.get("triggered"):
                continue
            alerts.append(
                {
                    "id": f"{row['id']}:{sig.get('name')}",
                    "timestamp": created_at,
                    "event_id": event_val,
                    "player_id": player_id,
                    "layer": str(sig.get("name") or "signal"),
                    "score": float(sig.get("score") or 0.0),
                    "threshold": float(sig.get("threshold") or 0.0),
                    "description": (sig.get("reasons") or ["Signal threshold exceeded"])[0],
                    "audit_id": row["id"],
                }
            )

    games = list(game_map.values())
    games.sort(key=lambda x: (-float(x["weighted_risk_score"]), -_risk_rank(x["risk_tier"]), x["created_at"]), reverse=False)
    alerts.sort(key=lambda x: x["timestamp"], reverse=True)

    elevated_count = len([g for g in games if _risk_rank(g["risk_tier"]) >= 3])
    avg_regan = 0.0
    if rows:
        regans = [float((r.get("response", {}) or {}).get("regan_z_score") or 0.0) for r in rows]
        avg_regan = sum(regans) / len(regans) if regans else 0.0

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "games": games,
        "alerts": alerts[:300],
        "summary": {
            "total_games_analyzed_today": len(rows),
            "games_elevated_or_above": elevated_count,
            "awaiting_review_count": len(alerts),
            "average_regan_z_score": round(avg_regan, 4),
        },
    }


@app.get("/v1/system-status", response_model=SystemStatusResponse)
def system_status_endpoint(
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> SystemStatusResponse:
    authorize_action(x_role, "system_status")
    return SystemStatusResponse(**system_status())


def _run_analysis(
    req: AnalyzeRequest,
    *,
    federation_id: str | None = None,
    pgn_text: str | None = None,
    parsed_games: list[dict] | None = None,
    player_color: str | None = None,
    opponent_player_id: str | None = None,
) -> AnalyzeResponse:
    features = compute_features(req)
    if req.high_stakes_event and not features.timing_available:
        raise HTTPException(
            status_code=400,
            detail="High-stakes event requires clock data (%clk) in PGN/move inputs",
        )

    layers = evaluate_all_layers(features)
    tier, conf, explanation, weighted_score, fusion_meta = classify_with_meta(features, layers)
    explainability_method, explainability_items = build_explainability(features, layers, weighted_score, fusion_meta)

    if features.analyzed_move_count == 0:
        explanation.append("No non-trivial positions after opening/endgame/forced filtering")

    explanation.extend(r for l in layers for r in l.reasons)

    human_explanations: list[str] = []
    if features.regan_z_score > features.regan_threshold:
        human_explanations.append(
            "The player's performance exceeded what is statistically expected for their rating band."
        )
    if features.time_variance_anomaly_score and features.time_variance_anomaly_score > 0.8:
        human_explanations.append(
            "Move timing patterns appear unusually consistent relative to expected human variability."
        )
    if features.complexity_accuracy_ratio and features.complexity_accuracy_ratio > 1.2:
        human_explanations.append(
            "Accuracy in complex positions is higher than expected for this rating band."
        )
    if not human_explanations:
        human_explanations.append("Observed play is within expected statistical variation for similar-rated players.")

    evidence_report = build_evidence_report(req, features, layers, weighted_score, fusion_meta)
    environmental_metrics = {}
    identity_confidence = {}
    if isinstance(req.behavioral, dict):
        env = req.behavioral.get("environment")
        if isinstance(env, dict):
            environmental_metrics = env
        camera_summary = req.behavioral.get("camera_summary")
        if isinstance(camera_summary, dict):
            environmental_metrics = {**environmental_metrics, "camera_summary": camera_summary}
        identity = req.behavioral.get("identity_confidence")
        if isinstance(identity, dict):
            identity_confidence = identity

    response_payload = {
        "player_id": req.player_id,
        "event_id": req.event_id,
        "risk_tier": tier.value,
        "confidence": conf,
        "analyzed_move_count": features.analyzed_move_count,
        "triggered_signals": len([l for l in layers if l.triggered]),
        "weighted_risk_score": weighted_score,
        "signals": [
            {
                "name": l.name,
                "triggered": l.triggered,
                "score": round(float(l.score), 4),
                "threshold": round(float(l.threshold), 4),
                "reasons": l.reasons,
            }
            for l in layers
        ],
        "explanation": explanation,
        "human_explanations": human_explanations,
        "model_version": settings.model_version,
        "feature_schema_version": settings.feature_schema_version,
        "report_schema_version": settings.report_schema_version,
        "natural_occurrence_statement": natural_occurrence_statement(features.regan_z_score, features.regan_threshold),
        "natural_occurrence_probability": natural_occurrence_probability(features.regan_z_score, features.regan_threshold),
        "regan_z_score": features.regan_z_score,
        "regan_threshold": features.regan_threshold,
        "pep_score": features.pep_score,
        "superhuman_move_rate": features.superhuman_move_rate,
        "rating_adjusted_move_probability": features.rating_adjusted_move_probability,
        "opening_familiarity_index": features.opening_familiarity_index,
        "opponent_strength_correlation": features.opponent_strength_correlation,
        "round_anomaly_clustering_score": features.round_anomaly_clustering_score,
        "complex_blunder_rate": features.complex_blunder_rate,
        "zero_blunder_in_complex_games_flag": features.zero_blunder_in_complex_games_flag,
        "move_quality_uniformity_score": features.move_quality_uniformity_score,
        "time_variance_anomaly_score": features.time_variance_anomaly_score,
        "time_clustering_anomaly_flag": features.time_clustering_anomaly_flag,
        "break_timing_correlation": features.break_timing_correlation,
        "timing_confidence_score": features.timing_confidence_score,
        "stockfish_maia_divergence": features.stockfish_maia_divergence,
        "maia_humanness_score": features.maia_humanness_score,
        "maia_personalization_confidence": features.maia_personalization_confidence,
        "maia_model_version": features.maia_model_version,
        "rolling_12m_weighted_acl": features.rolling_12m_weighted_acl,
        "historical_volatility_score": features.historical_volatility_score,
        "opponent_pool_adjustment": features.opponent_pool_adjustment,
        "multi_tournament_anomaly_score": features.multi_tournament_anomaly_score,
        "career_growth_curve_score": features.career_growth_curve_score,
        "ml_fusion_source": str(fusion_meta.get("source") or "heuristic_only"),
        "ml_primary_score": (
            float(fusion_meta["primary_score"]) if fusion_meta.get("primary_score") is not None else None
        ),
        "ml_secondary_score": (
            float(fusion_meta["secondary_score"]) if fusion_meta.get("secondary_score") is not None else None
        ),
        "confidence_intervals": {
            k: ([float(v[0]), float(v[1])] if v is not None else None) for k, v in features.confidence_intervals.items()
        },
        "evidence_report": evidence_report,
        "behavioral_metrics": {
            "copy_paste_events": int(features.behavioral_copy_paste_events),
            "focus_loss_count": int(features.behavioral_focus_loss_count),
            "tab_switch_count": int(features.behavioral_tab_switch_count),
            "avg_mouse_path_straightness": float(features.behavioral_avg_mouse_path_straightness),
            "avg_move_time_seconds": float(features.behavioral_avg_move_time_seconds),
            "mouse_event_count": int(features.behavioral_mouse_event_count),
            "avg_drag_duration_ms": float(features.behavioral_avg_drag_duration_ms),
            "avg_hover_dwell_played_square_ms": float(features.behavioral_avg_hover_dwell_played_square_ms),
            "avg_squares_visited": float(features.behavioral_avg_squares_visited),
            "avg_reaction_time_ms": float(features.behavioral_avg_reaction_time_ms),
        },
        "environmental_metrics": environmental_metrics,
        "identity_confidence": identity_confidence,
    }

    request_payload = req.model_dump()
    audit_id = audit_repo.write({"request": request_payload, "response": response_payload}, model_version=settings.model_version)
    report_state = audit_repo.get_report_workflow(audit_id)
    response_payload["explainability_method"] = explainability_method
    response_payload["explainability_items"] = explainability_items
    response_payload["legal_disclaimer_text"] = settings.legal_disclaimer_text
    response_payload["legal_disclaimer_enforced"] = bool(settings.legal_disclaimer_text.strip())
    response_payload["report_version"] = int(report_state["report_version"])
    response_payload["report_locked"] = bool(report_state["report_locked"])
    response_payload["report_locked_at"] = report_state["report_locked_at"]

    try:
        profile = {
            "player_id": req.player_id,
            "last_event_id": req.event_id,
            "last_risk_tier": response_payload["risk_tier"],
            "last_weighted_risk_score": response_payload["weighted_risk_score"],
            "last_analyzed_move_count": response_payload["analyzed_move_count"],
            "updated_at": datetime.now(UTC).isoformat(),
        }
        investigation_repo.upsert_player_profile(req.player_id, profile)
        investigation_repo.add_player_history(
            req.player_id,
            req.event_id,
            {
                "created_at": datetime.now(UTC).isoformat(),
                "risk_tier": response_payload["risk_tier"],
                "weighted_risk_score": response_payload["weighted_risk_score"],
                "analyzed_move_count": response_payload["analyzed_move_count"],
                "event_id": req.event_id,
            },
        )
    except Exception:
        pass

    persisted_to_supabase = False
    if supabase_repo is not None:
        try:
            supabase_repo.persist_analysis(
                player_id=req.player_id,
                event_id=req.event_id,
                federation_id=federation_id,
                audit_id=audit_id,
                weighted_risk_score=weighted_score,
                model_version=settings.model_version,
                feature_schema_version=settings.feature_schema_version,
                report_schema_version=settings.report_schema_version,
                legal_disclaimer_text=settings.legal_disclaimer_text,
                human_review_required=(tier.value == "HIGH_STATISTICAL_ANOMALY"),
                event_type=req.event_type,
                regan_threshold_used=features.regan_threshold,
                natural_occurrence_statement=response_payload["natural_occurrence_statement"],
                natural_occurrence_probability=response_payload["natural_occurrence_probability"],
                response_payload=response_payload,
                request_payload=request_payload,
            )
            if pgn_text is not None and parsed_games and player_color and opponent_player_id:
                supabase_repo.persist_pgn_details(
                    event_id=req.event_id,
                    federation_id=federation_id,
                    player_id=req.player_id,
                    opponent_player_id=opponent_player_id,
                    player_color=player_color,
                    pgn_text=pgn_text,
                    parsed_games=parsed_games,
                )
            persisted_to_supabase = True
        except Exception as exc:
            if settings.persistence_fail_hard:
                raise HTTPException(
                    status_code=500,
                    detail=f"Supabase persistence failed: {supabase_repo.error_text(exc)}",
                ) from exc
            explanation.append(f"Supabase persistence warning: {supabase_repo.error_text(exc)}")

    return AnalyzeResponse(**response_payload, audit_id=audit_id, persisted_to_supabase=persisted_to_supabase)


@app.post("/v1/analyze", response_model=AnalyzeResponse)
def analyze(
    req: AnalyzeRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
    x_federation_id: Annotated[str | None, Header(alias="X-Federation-Id")] = None,
) -> AnalyzeResponse:
    role = authorize_action(x_role, "analyze")
    enforce_tenant_scope(role, x_federation_id, req.event_id)
    return _run_analysis(req, federation_id=x_federation_id)


@app.post("/v1/analyze-pgn", response_model=AnalyzeResponse)
def analyze_pgn(
    req: AnalyzePgnRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
    x_federation_id: Annotated[str | None, Header(alias="X-Federation-Id")] = None,
) -> AnalyzeResponse:
    role = authorize_action(x_role, "analyze_pgn")
    enforce_tenant_scope(role, x_federation_id, req.event_id)
    games = parse_pgn_games(req.pgn_text)
    if not games:
        raise HTTPException(status_code=400, detail="No PGN games parsed from pgn_text")

    try:
        ctx = create_engine_context(req.official_elo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        parsed_games = [
            game_to_inputs(
                game=g,
                game_id=f"{req.event_id}:{req.player_id}:pgn-{idx+1}",
                player_color=req.player_color,
                ctx=ctx,
            )
            for idx, g in enumerate(games)
        ]
    finally:
        ctx.close()

    normalized = AnalyzeRequest(
        player_id=req.player_id,
        event_id=req.event_id,
        event_type=req.event_type,
        official_elo=req.official_elo,
        high_stakes_event=req.high_stakes_event,
        performance_rating_this_event=req.performance_rating_this_event,
        games=parsed_games,
        historical=req.historical,
    )
    return _run_analysis(
        normalized,
        federation_id=x_federation_id,
        pgn_text=req.pgn_text,
        parsed_games=[g.model_dump() for g in parsed_games],
        player_color=req.player_color,
        opponent_player_id=req.opponent_player_id,
    )


@app.post("/v1/tournament-summary", response_model=TournamentSummaryResponse)
def tournament_summary(
    req: Union[AnalyzeRequest, AnalyzePgnRequest],
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
    x_federation_id: Annotated[str | None, Header(alias="X-Federation-Id")] = None,
) -> TournamentSummaryResponse:
    role = authorize_action(x_role, "tournament_summary")
    req_event_id = req.event_id
    enforce_tenant_scope(role, x_federation_id, req_event_id)
    if isinstance(req, AnalyzePgnRequest):
        games = parse_pgn_games(req.pgn_text)
        if not games:
            raise HTTPException(status_code=400, detail="No PGN games parsed from pgn_text")

        try:
            ctx = create_engine_context(req.official_elo)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        try:
            parsed_games = [
                game_to_inputs(
                    game=g,
                    game_id=f"{req.event_id}:{req.player_id}:pgn-{idx+1}",
                    player_color=req.player_color,
                    ctx=ctx,
                )
                for idx, g in enumerate(games)
            ]
        finally:
            ctx.close()

        req = AnalyzeRequest(
            player_id=req.player_id,
            event_id=req.event_id,
            event_type=req.event_type,
            official_elo=req.official_elo,
            high_stakes_event=req.high_stakes_event,
            performance_rating_this_event=req.performance_rating_this_event,
            games=parsed_games,
            historical=req.historical,
        )

    overall = compute_features(req)
    per_game = []
    for g in req.games:
        one = AnalyzeRequest(
            player_id=req.player_id,
            event_id=req.event_id,
            event_type=req.event_type,
            official_elo=req.official_elo,
            high_stakes_event=req.high_stakes_event,
            performance_rating_this_event=req.performance_rating_this_event,
            games=[g],
            historical=req.historical,
        )
        fg = compute_features(one)
        per_game.append(
            {
                "game_id": g.game_id,
                "analyzed_move_count": fg.analyzed_move_count,
                "ipr_estimate": fg.ipr_estimate,
                "pep_score": fg.pep_score,
                "regan_z_score": fg.regan_z_score,
                "regan_threshold": fg.regan_threshold,
            }
        )

    return TournamentSummaryResponse(
        player_id=req.player_id,
        event_id=req.event_id,
        event_type=req.event_type,
        games_count=len(req.games),
        analyzed_move_count=overall.analyzed_move_count,
        ipr_estimate=overall.ipr_estimate,
        pep_score=overall.pep_score,
        regan_z_score=overall.regan_z_score,
        regan_threshold=overall.regan_threshold,
        confidence_intervals={
            k: ([float(v[0]), float(v[1])] if v is not None else None) for k, v in overall.confidence_intervals.items()
        },
        per_game=per_game,
    )


@app.get("/v1/reports/{audit_id}")
def report_status(
    audit_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "report_get")
    return audit_repo.get_report_workflow(audit_id)


@app.post("/v1/reports/{audit_id}/lock")
def report_lock(
    audit_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "report_lock")
    return audit_repo.lock_report(audit_id)


@app.post("/v1/reports/{audit_id}/version")
def report_version_bump(
    audit_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "report_version")
    try:
        return audit_repo.bump_report_version(audit_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/v1/audit/{audit_id}")
def get_audit(
    audit_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "report_get")
    audit = audit_repo.get(audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


def _auto_flags_from_analysis(response: dict) -> list[dict]:
    flags: list[dict] = []
    if float(response.get("superhuman_move_rate") or 0.0) > 0.25:
        flags.append(
            {
                "flag_type": "high_superhuman_rate",
                "severity": "high",
                "message": "High consistency in complex positions detected.",
                "metadata": {"superhuman_move_rate": response.get("superhuman_move_rate")},
            }
        )
    if float(response.get("time_variance_anomaly_score") or 0.0) > 0.8:
        flags.append(
            {
                "flag_type": "timing_anomaly",
                "severity": "medium",
                "message": "Unusual timing pattern detected.",
                "metadata": {"time_variance_anomaly_score": response.get("time_variance_anomaly_score")},
            }
        )
    if float(response.get("engine_maia_disagreement") or 0.0) > 0.35:
        flags.append(
            {
                "flag_type": "engine_maia_disagreement",
                "severity": "medium",
                "message": "Engine vs Maia divergence is elevated.",
                "metadata": {"engine_maia_disagreement": response.get("engine_maia_disagreement")},
            }
        )
    for sig in response.get("signals", []):
        if sig.get("triggered"):
            flags.append(
                {
                    "flag_type": f"signal_{sig.get('name')}",
                    "severity": "low",
                    "message": f"Signal triggered: {sig.get('name')}",
                    "metadata": {"score": sig.get("score"), "threshold": sig.get("threshold")},
                }
            )
    return flags


def _require_partner_key(api_key: str | None) -> dict:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing x-api-key")
    key = partner_repo.find_key(api_key)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid x-api-key")
    return key


def _rate_limit_or_429(api_key: str, limit: int) -> None:
    if not rate_limiter.allow(api_key, limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.post("/v1/cases")
def create_case(
    req: CaseCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_create")
    return investigation_repo.create_case(
        title=req.title,
        status="opened",
        players=req.players,
        event_id=req.event_id,
        summary=req.summary,
        tags=req.tags,
        priority=req.priority,
        assigned_to=req.assigned_to,
    )


@app.get("/v1/cases")
def list_cases(
    limit: int = 200,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_list")
    return {"cases": investigation_repo.list_cases(limit=limit)}


@app.get("/v1/cases/{case_id}")
def get_case(
    case_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_get")
    try:
        case = investigation_repo.get_case(case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return case


@app.post("/v1/cases/{case_id}/status")
def update_case_status(
    case_id: str,
    req: CaseStatusUpdateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_update")
    try:
        return investigation_repo.update_case_status(case_id, req.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/cases/{case_id}/notes")
def add_case_note(
    case_id: str,
    req: CaseNoteCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_note_add")
    return investigation_repo.add_note(case_id, req.author, req.note_type, req.structured, req.text)


@app.get("/v1/cases/{case_id}/notes")
def list_case_notes(
    case_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_note_list")
    return {"notes": investigation_repo.list_notes(case_id)}


@app.post("/v1/cases/{case_id}/evidence")
def add_case_evidence(
    case_id: str,
    req: CaseEvidenceCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_evidence_add")
    return investigation_repo.add_evidence(case_id, req.evidence_type, req.label, req.path, req.metadata)


@app.get("/v1/cases/{case_id}/evidence")
def list_case_evidence(
    case_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_evidence_list")
    return {"evidence": investigation_repo.list_evidence(case_id)}


@app.post("/v1/cases/{case_id}/flags")
def add_case_flag(
    case_id: str,
    req: CaseFlagCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_flag_add")
    return investigation_repo.add_flag(case_id, req.flag_type, req.severity, req.message, req.metadata)


@app.get("/v1/cases/{case_id}/flags")
def list_case_flags(
    case_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_flag_list")
    return {"flags": investigation_repo.list_flags(case_id)}


@app.post("/v1/cases/{case_id}/auto-flags")
def auto_case_flags(
    case_id: str,
    audit_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "case_flag_add")
    audit = audit_repo.get(audit_id)
    if audit is None:
        raise HTTPException(status_code=404, detail="Audit record not found")
    flags = _auto_flags_from_analysis(audit.get("response", {}))
    saved = [investigation_repo.add_flag(case_id, f["flag_type"], f["severity"], f["message"], f["metadata"]) for f in flags]
    return {"flags": saved}


@app.post("/v1/otb/incidents")
def create_otb_incident(
    req: OTBIncidentCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_incident_create")
    return investigation_repo.add_otb_incident(
        case_id=req.case_id,
        event_id=req.event_id,
        player_id=req.player_id,
        incident_type=req.incident_type,
        severity=req.severity,
        description=req.description,
        occurred_at=req.occurred_at,
        metadata=req.metadata,
    )


@app.get("/v1/otb/incidents")
def list_otb_incidents(
    case_id: str | None = None,
    event_id: str | None = None,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_incident_list")
    return {"incidents": investigation_repo.list_otb_incidents(case_id=case_id, event_id=event_id)}


@app.post("/v1/otb/camera-events")
def ingest_otb_camera_events(
    req: OTBCameraEventRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_camera_ingest")
    storage_mode = (req.storage_mode or "safe").lower()
    consent = req.consent or {}
    consent_given = bool(consent.get("camera_raw") or consent.get("raw_camera") or consent.get("camera"))
    if storage_mode == "raw":
        if not settings.camera_raw_storage_enabled:
            raise HTTPException(status_code=403, detail="Raw camera storage disabled")
        if settings.consent_required_for_raw and not consent_given:
            raise HTTPException(status_code=422, detail="Camera raw storage requires consent")

    events = req.events or []
    summary = req.summary or {}
    if not summary and events:
        summary = summarize_camera_events(events)
    if storage_mode != "raw":
        events = []
    record = investigation_repo.add_otb_camera_event(
        event_id=req.event_id,
        case_id=req.case_id,
        player_id=req.player_id,
        session_id=req.session_id,
        camera_id=req.camera_id,
        storage_mode=storage_mode,
        consent=consent,
        events=events,
        summary=summary,
    )
    return {"status": "ok", "record": record}


@app.post("/v1/otb/camera-service/event")
def ingest_camera_service_event(
    req: CameraServiceEventPayload,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_camera_ingest")
    storage_mode = (req.storage_mode or "safe").lower()
    consent = req.consent or {}
    consent_given = bool(consent.get("camera_raw") or consent.get("raw_camera") or consent.get("camera"))
    if storage_mode == "raw":
        if not settings.camera_raw_storage_enabled:
            raise HTTPException(status_code=403, detail="Raw camera storage disabled")
        if settings.consent_required_for_raw and not consent_given:
            raise HTTPException(status_code=422, detail="Camera raw storage requires consent")

    payload = req.model_dump(by_alias=True)
    events = [payload]
    summary = summarize_camera_events(events)
    if storage_mode != "raw":
        events = []
    record = investigation_repo.add_otb_camera_event(
        event_id=req.event_id,
        case_id=req.case_id,
        player_id=req.player_id,
        session_id=req.session_id,
        camera_id=req.device_id,
        storage_mode=storage_mode,
        consent=consent,
        events=events,
        summary=summary,
    )
    return {"status": "ok", "record": record}


@app.get("/v1/otb/camera-events")
def list_otb_camera_events(
    event_id: str | None = None,
    case_id: str | None = None,
    player_id: str | None = None,
    session_id: str | None = None,
    limit: int = 200,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_camera_list")
    return {
        "events": investigation_repo.list_otb_camera_events(
            event_id=event_id, case_id=case_id, player_id=player_id, session_id=session_id, limit=limit
        )
    }


@app.post("/v1/otb/board-events")
def ingest_dgt_board_event(
    req: DGTBoardEventRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_board_ingest")
    record = investigation_repo.add_dgt_board_event(
        event_id=req.event_id,
        session_id=req.session_id,
        board_serial=req.board_serial,
        move_uci=req.move_uci,
        ply=req.ply,
        fen=req.fen,
        clock_ms=req.clock_ms,
        raw=req.raw,
    )
    if req.session_id and req.move_uci and req.ply is not None:
        try:
            investigation_repo.add_live_move(
                session_id=req.session_id,
                ply=int(req.ply),
                move_uci=req.move_uci,
                time_spent=None,
                clock_remaining=(float(req.clock_ms) / 1000.0) if req.clock_ms else None,
                complexity=None,
                engine_match=None,
                maia_prob=None,
                tags={"source": "dgt"},
            )
        except Exception:
            pass
    return {"status": "ok", "record": record}


@app.get("/v1/otb/board-events")
def list_dgt_board_events(
    event_id: str | None = None,
    session_id: str | None = None,
    limit: int = 200,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "otb_board_list")
    return {
        "events": investigation_repo.list_dgt_board_events(
            event_id=event_id, session_id=session_id, limit=limit
        )
    }


@app.post("/v1/reports/generate")
def generate_report(
    req: ReportGenerateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
):
    authorize_action(x_role, "report_generate")
    if not req.audit_id and not req.case_id:
        raise HTTPException(status_code=400, detail="audit_id or case_id is required")
    analysis = {}
    notes: list[dict] = []
    if req.audit_id:
        audit = audit_repo.get(req.audit_id)
        if audit is None:
            raise HTTPException(status_code=404, detail="Audit record not found")
        analysis = audit.get("response", {})
    if req.case_id:
        try:
            notes = investigation_repo.list_notes(req.case_id)
        except KeyError:
            notes = []
    evidence = analysis.get("evidence_report") if isinstance(analysis, dict) else None
    report = build_structured_report(analysis, evidence, notes, req.mode)
    if req.use_ai:
        narrative = build_ai_narrative(
            analysis,
            evidence,
            notes,
            req.mode,
            provider=req.llm_provider,
            model=req.llm_model,
        )
        if narrative:
            report["narrative_sections"] = narrative
    report["pdf_engine"] = req.pdf_engine or settings.report_pdf_engine

    if req.export_format == "csv":
        content = report_to_csv(report)
        record = investigation_repo.add_report(req.case_id, req.audit_id, req.report_type, req.mode, "csv", report, content)
        return Response(content=content, media_type="text/csv", headers={"X-Report-Id": record["id"]})
    if req.export_format == "pdf":
        pdf_bytes = report_to_pdf(report)
        record = investigation_repo.add_report(req.case_id, req.audit_id, req.report_type, req.mode, "pdf", report, None)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"X-Report-Id": record["id"]})

    record = investigation_repo.add_report(req.case_id, req.audit_id, req.report_type, req.mode, "json", report, None)
    return record


@app.get("/v1/reports/generated/{report_id}")
def get_generated_report(
    report_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "report_get")
    try:
        return investigation_repo.get_report(report_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/partner/analyze")
def partner_analyze(
    req: PartnerAnalyzeRequest,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
) -> dict:
    key = _require_partner_key(x_api_key)
    _rate_limit_or_429(x_api_key or "", int(key.get("rate_limit_per_minute") or 60))
    status = system_status()
    if not status.get("analysis_pipeline_operational"):
        raise HTTPException(status_code=503, detail="Analysis pipeline unavailable")

    camera_mode = (req.camera_storage_mode or "safe").lower()
    consent = req.consent or {}
    consent_given = bool(consent.get("camera_raw") or consent.get("raw_camera") or consent.get("camera"))
    if camera_mode == "raw":
        if not settings.camera_raw_storage_enabled:
            raise HTTPException(status_code=403, detail="Raw camera storage disabled")
        if settings.consent_required_for_raw and not consent_given:
            raise HTTPException(status_code=422, detail="Camera raw storage requires consent")

    games = parse_pgn_games(req.pgn)
    if not games:
        raise HTTPException(status_code=422, detail="Invalid PGN payload")

    job_id = f"job_{secrets.token_hex(8)}"
    payload = req.model_dump()
    device_fp = payload.get("device_fingerprint") or {}
    if isinstance(device_fp, dict):
        fp_hash = device_fp.get("fingerprint_hash")
        if not fp_hash and device_fp.get("fingerprint_raw"):
            fp_hash = hash_key(str(device_fp.get("fingerprint_raw")))
        if fp_hash:
            device_fp["fingerprint_hash"] = fp_hash
        device_fp.pop("fingerprint_raw", None)
        payload["device_fingerprint"] = device_fp

    if camera_mode != "raw":
        payload["camera_summary"] = summarize_camera_events(payload.get("camera_events") or [])
        payload["camera_events"] = []
        payload["camera_storage_mode"] = "safe"

    job = partner_repo.create_job(
        job_id=job_id,
        api_key_id=key["id"],
        game_id=req.game_id,
        player_id=req.player_id,
        raw_payload=payload,
        webhook_url=key.get("webhook_url"),
    )
    if supabase_repo is not None:
        try:
            supabase_repo.persist_partner_job(
                job_id=job_id,
                api_key_id=key["id"],
                game_id=req.game_id,
                player_id=req.player_id,
                raw_payload=req.model_dump(),
                status="queued",
                webhook_url=key.get("webhook_url"),
            )
        except Exception:
            pass
    try:
        if payload.get("camera_events") or payload.get("camera_summary"):
            events = payload.get("camera_events") or [payload.get("camera_summary")]
            partner_repo.add_camera_events(
                job_id,
                camera_mode,
                events if isinstance(events, list) else [events],
                consent,
            )
        if consent:
            partner_repo.add_consent_log(job_id, key["id"], "camera_raw", consent_given, consent)
    except Exception:
        pass

    partner_worker.enqueue(job_id)
    return {
        "status": "accepted",
        "job_id": job_id,
        "message": "Analysis queued. Results will be delivered to your callback URL.",
    }


@app.get("/v1/partner/result/{job_id}")
def partner_result(
    job_id: str,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
) -> dict:
    key = _require_partner_key(x_api_key)
    job = partner_repo.get_job(job_id)
    if not job or job.get("api_key_id") != key["id"]:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.get("job_id"),
        "status": job.get("status"),
        "result": job.get("result"),
        "risk_level": job.get("risk_level"),
        "risk_score": job.get("risk_score"),
    }


@app.post("/v1/partner/webhook/register")
def partner_register_webhook(
    req: PartnerWebhookRegisterRequest,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
) -> dict:
    key = _require_partner_key(x_api_key)
    return partner_repo.update_webhook(key["id"], req.webhook_url)


@app.get("/v1/partner/keys")
def list_partner_keys(
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "partner_key_list")
    return {"keys": partner_repo.list_keys()}


@app.post("/v1/partner/keys/create")
def create_partner_key(
    req: PartnerKeyCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "partner_key_create")
    api_key, secret = generate_keypair()
    try:
        return partner_repo.create_key(
            key=api_key,
            secret=secret,
            partner_name=req.partner_name,
            webhook_url=req.webhook_url,
            rate_limit_per_minute=req.rate_limit_per_minute,
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.delete("/v1/partner/keys/{key_id}")
def disable_partner_key(
    key_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "partner_key_disable")
    try:
        return partner_repo.disable_key(key_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/partner/keys/{key_id}/rotate")
def rotate_partner_key(
    key_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "partner_key_rotate")
    api_key, secret = generate_keypair()
    try:
        updated = partner_repo.rotate_secret(key_id, secret)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    updated["secret"] = secret
    return updated


@app.post("/v1/partner/session/create")
def create_partner_session(
    req: PartnerSessionCreateRequest,
    x_api_key: Annotated[str | None, Header(alias="x-api-key")] = None,
) -> dict:
    key = _require_partner_key(x_api_key)
    session_id = f"sess_{secrets.token_hex(8)}"
    partner_repo.create_session(session_id, key["id"], req.game_id, req.player_id)
    investigation_repo.create_live_session(req.game_id, [req.player_id or "unknown"])
    return {"session_id": session_id}


@app.post("/v1/visuals/pgn")
def visuals_from_pgn(
    req: VisualsRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "visuals")
    return build_visuals_from_game(req.game, req.official_elo)


@app.post("/v1/visuals/analyze-pgn")
def visuals_from_analyze_pgn(
    req: AnalyzePgnRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "visuals")
    games = parse_pgn_games(req.pgn_text)
    if not games:
        raise HTTPException(status_code=400, detail="No PGN games parsed from pgn_text")
    try:
        ctx = create_engine_context(req.official_elo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        parsed = game_to_inputs(
            game=games[0],
            game_id=f"{req.event_id}:{req.player_id}:visuals",
            player_color=req.player_color,
            ctx=ctx,
        )
    finally:
        ctx.close()
    return build_visuals_from_game(parsed, req.official_elo)


@app.get("/v1/tournament-dashboard", response_model=TournamentDashboardResponse)
def tournament_dashboard(
    event_id: str | None = None,
    limit: int = 200,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> TournamentDashboardResponse:
    authorize_action(x_role, "tournament_dashboard")
    rows = audit_repo.recent(limit=limit, event_id=event_id)
    agg: dict[str, list[float]] = {}
    tiers: dict[str, str] = {}
    for row in rows:
        resp = row.get("response", {})
        key = str(resp.get("player_id") or "unknown")
        agg.setdefault(key, []).append(float(resp.get("weighted_risk_score") or 0.0))
        tiers[key] = str(resp.get("risk_tier") or "LOW")
    players = [
        {"player_id": pid, "avg_risk_score": round(sum(vals) / max(1, len(vals)), 4), "risk_tier": tiers.get(pid)}
        for pid, vals in agg.items()
    ]
    players.sort(key=lambda x: x["avg_risk_score"], reverse=True)
    alerts = [{"message": f"Top suspicious player: {p['player_id']}", "score": p["avg_risk_score"]} for p in players[:3]]
    return TournamentDashboardResponse(event_id=event_id, players=players, alerts=alerts)


@app.get("/v1/players/{player_id}/profile", response_model=PlayerProfileResponse)
def player_profile(
    player_id: str,
    limit: int = 200,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> PlayerProfileResponse:
    authorize_action(x_role, "player_profile")
    stored_profile = investigation_repo.get_player_profile(player_id)
    history_rows = investigation_repo.list_player_history(player_id, limit=limit)
    profile = stored_profile["profile"] if stored_profile else {}
    return PlayerProfileResponse(
        player_id=player_id,
        updated_at=stored_profile["updated_at"] if stored_profile else None,
        profile=profile,
        history=history_rows,
    )


@app.post("/v1/live/sessions")
def create_live_session(
    req: LiveSessionCreateRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "live_create")
    return investigation_repo.create_live_session(req.event_id, req.players)


@app.get("/v1/live/sessions/{session_id}")
def get_live_session(
    session_id: str,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "live_get")
    try:
        return investigation_repo.get_live_session(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/live/moves")
def ingest_live_move(
    req: LiveMoveIngestRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "live_ingest")
    return investigation_repo.add_live_move(
        req.session_id,
        req.ply,
        req.move_uci,
        req.time_spent,
        req.clock_remaining,
        req.complexity,
        req.engine_match,
        req.maia_prob,
        req.tags,
    )


@app.get("/v1/live/sessions/{session_id}/risk")
def live_risk(
    session_id: str,
    limit: int = 100,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
) -> dict:
    authorize_action(x_role, "live_risk")
    moves = investigation_repo.list_live_moves(session_id, limit=limit)
    return compute_live_risk(moves)


@app.post("/v1/demo/analyze")
def demo_analyze(
    req: AnalyzePgnRequest,
    x_role: Annotated[str, Header(alias="X-Role")] = "system_admin",
):
    authorize_action(x_role, "demo_analyze")
    analysis = analyze_pgn(req, x_role=x_role)
    report = build_structured_report(analysis.model_dump(), analysis.evidence_report.model_dump() if analysis.evidence_report else None, [], "arbiter")
    visuals = {}
    if analysis.analyzed_move_count and req.pgn_text:
        games = parse_pgn_games(req.pgn_text)
        if games:
            try:
                ctx = create_engine_context(req.official_elo)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            try:
                inputs = game_to_inputs(games[0], game_id=f"{req.event_id}:{req.player_id}:demo", player_color=req.player_color, ctx=ctx)
            finally:
                ctx.close()
            visuals = build_visuals_from_game(inputs, req.official_elo)
    return {"analysis": analysis, "report": report, "visuals": visuals}


@app.websocket("/ws/live/{session_id}")
async def live_ws(websocket: WebSocket, session_id: str):
    api_key = websocket.query_params.get("api_key")
    role = websocket.query_params.get("role", "system_admin")
    if api_key:
        try:
            _require_partner_key(api_key)
        except HTTPException:
            await websocket.close(code=4401)
            return
    else:
        try:
            authorize_action(role, "live_get")
        except HTTPException:
            await websocket.close(code=4403)
            return

    await live_connections.connect(session_id, websocket)
    try:
        while True:
            payload = await websocket.receive_json()
            event_type = str(payload.get("type") or "event")
            if event_type == "move":
                investigation_repo.add_live_move(
                    session_id=session_id,
                    ply=int(payload.get("ply") or 0),
                    move_uci=str(payload.get("uci") or ""),
                    time_spent=float(payload.get("time_spent") or 0.0) if payload.get("time_spent") is not None else None,
                    clock_remaining=float(payload.get("clock") or 0.0) if payload.get("clock") is not None else None,
                    complexity=float(payload.get("complexity") or 0.0) if payload.get("complexity") is not None else None,
                    engine_match=float(payload.get("engine_match") or 0.0) if payload.get("engine_match") is not None else None,
                    maia_prob=float(payload.get("maia_prob") or 0.0) if payload.get("maia_prob") is not None else None,
                    tags=payload,
                )
            if event_type == "game_end" and payload.get("pgn") and api_key:
                analyze_req = PartnerAnalyzeRequest(
                    game_id=str(payload.get("game_id") or session_id),
                    player_id=str(payload.get("player_id") or "unknown"),
                    player_color=str(payload.get("player_color") or "white"),
                    pgn=str(payload.get("pgn")),
                )
                try:
                    partner_analyze(analyze_req, x_api_key=api_key)
                except Exception:
                    pass
            await live_connections.broadcast(session_id, payload)
    except WebSocketDisconnect:
        live_connections.disconnect(session_id, websocket)
