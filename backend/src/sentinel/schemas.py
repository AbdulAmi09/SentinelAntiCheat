from __future__ import annotations

from typing import Any

<<<<<<< HEAD
from pydantic import BaseModel, ConfigDict, Field
=======
from pydantic import BaseModel, Field
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674


class MoveInput(BaseModel):
    ply: int
    engine_best: str
    player_move: str
    cp_loss: float = Field(ge=0)
    top3_match: bool = False
    maia_probability: float | None = Field(default=None, ge=0, le=1)
    engine_rank: int | None = Field(default=None, ge=1)
    legal_move_count: int | None = Field(default=None, ge=1)
    complexity_score: int = Field(ge=0)
    candidate_moves_within_50cp: int = Field(ge=1)
    best_second_gap_cp: float = Field(default=0, ge=0)
    eval_swing_cp: float = Field(default=0, ge=0)
    best_eval_cp: float = 0
    played_eval_cp: float = 0
    is_opening_book: bool = False
    is_tablebase: bool = False
    is_forced: bool = False
    time_spent_seconds: float | None = Field(default=None, ge=0)


class GameInput(BaseModel):
    game_id: str
    opponent_official_elo: int | None = None
    moves: list[MoveInput]


class HistoricalProfile(BaseModel):
    games_count: int = 0
    avg_acl: float | None = None
    std_acl: float | None = None
    avg_ipr: float | None = None
    std_ipr: float | None = None
    avg_perf: float | None = None
    std_perf: float | None = None


class AnalyzeRequest(BaseModel):
    player_id: str
    event_id: str
    event_type: str = Field(default="online", pattern="^(online|otb)$")
    official_elo: int
    high_stakes_event: bool = False
    performance_rating_this_event: float | None = None
    games: list[GameInput]
    historical: HistoricalProfile = Field(default_factory=HistoricalProfile)
    behavioral: dict[str, Any] = Field(default_factory=dict)


class AnalyzePgnRequest(BaseModel):
    player_id: str
    event_id: str
    event_type: str = Field(default="online", pattern="^(online|otb)$")
    opponent_player_id: str = "opponent-unknown"
<<<<<<< HEAD
    official_elo: int | None = None
=======
    official_elo: int
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    player_color: str = Field(default="white", pattern="^(white|black)$")
    high_stakes_event: bool = False
    pgn_text: str
    performance_rating_this_event: float | None = None
    historical: HistoricalProfile = Field(default_factory=HistoricalProfile)


class SignalOut(BaseModel):
    name: str
    triggered: bool
    score: float
    threshold: float
    reasons: list[str]


class EvidenceLayer(BaseModel):
    name: str
    status: str
    metrics: dict[str, float | str | bool | None]


class EvidenceReport(BaseModel):
    conclusion: str
    engine_match_percentage: float
    maia_agreement_percentage: float | None = None
    engine_maia_disagreement: float | None = None
    rating_band_index: int | None = None
    anomaly_score: float | None = None
    anomaly_source: str
    centipawn_loss_statistics: dict[str, float]
    position_difficulty_metrics: dict[str, float | int]
    analysis_layers: list[EvidenceLayer] = Field(default_factory=list)
    signals: list[SignalOut] = Field(default_factory=list)
    player_anomaly_scores: list[float] = Field(default_factory=list)
    player_anomaly_trend: float = 0.0
    player_anomaly_rolling_average: float = 0.0
    player_anomaly_spike_count: int = 0
    style_fingerprint: dict[str, float | int] = Field(default_factory=dict)
    behavioral_metrics: dict[str, float | int] = Field(default_factory=dict)
    environmental_metrics: dict[str, float | int | str | bool] = Field(default_factory=dict)
    identity_confidence: dict[str, float | int | str | bool] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    player_id: str
    event_id: str
    risk_tier: str
    confidence: float
    analyzed_move_count: int
    triggered_signals: int
    weighted_risk_score: float
    signals: list[SignalOut]
    explanation: list[str]
    human_explanations: list[str] = Field(default_factory=list)
    audit_id: str
    persisted_to_supabase: bool = False
    model_version: str | None = None
    feature_schema_version: str | None = None
    report_schema_version: str | None = None
    natural_occurrence_statement: str | None = None
    natural_occurrence_probability: float | None = None
<<<<<<< HEAD
    ipr_estimate: float | None = None
    regan_z_score: float | None = None
    regan_threshold: float | None = None
    pep_score: float | None = None
    engine_match_pct: float | None = None
    superhuman_move_rate: float | None = None
    rating_adjusted_move_probability: float | None = None
    complexity_accuracy_ratio: float | None = None
=======
    regan_z_score: float | None = None
    regan_threshold: float | None = None
    pep_score: float | None = None
    superhuman_move_rate: float | None = None
    rating_adjusted_move_probability: float | None = None
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    opening_familiarity_index: float | None = None
    opponent_strength_correlation: float | None = None
    round_anomaly_clustering_score: float | None = None
    complex_blunder_rate: float | None = None
    zero_blunder_in_complex_games_flag: bool | None = None
    move_quality_uniformity_score: float | None = None
    time_variance_anomaly_score: float | None = None
    time_clustering_anomaly_flag: bool | None = None
    break_timing_correlation: float | None = None
    timing_confidence_score: float | None = None
    stockfish_maia_divergence: float | None = None
    maia_humanness_score: float | None = None
    maia_personalization_confidence: float | None = None
    maia_model_version: str | None = None
    rolling_12m_weighted_acl: float | None = None
    historical_volatility_score: float | None = None
    opponent_pool_adjustment: float | None = None
    multi_tournament_anomaly_score: float | None = None
    career_growth_curve_score: float | None = None
    ml_fusion_source: str | None = None
    ml_primary_score: float | None = None
    ml_secondary_score: float | None = None
    explainability_method: str | None = None
    explainability_items: list[dict[str, float | str]] = Field(default_factory=list)
    legal_disclaimer_text: str | None = None
    legal_disclaimer_enforced: bool = False
    report_version: int = 1
    report_locked: bool = False
    report_locked_at: str | None = None
<<<<<<< HEAD
    regan_metrics: dict[str, float | int] | None = None
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    confidence_intervals: dict[str, list[float] | None] = Field(default_factory=dict)
    evidence_report: EvidenceReport | None = None
    behavioral_metrics: dict[str, float | int] = Field(default_factory=dict)
    environmental_metrics: dict[str, float | int | str | bool] = Field(default_factory=dict)
    identity_confidence: dict[str, float | int | str | bool] = Field(default_factory=dict)


class TournamentGameSummary(BaseModel):
    game_id: str
    analyzed_move_count: int
    ipr_estimate: float
    pep_score: float
    regan_z_score: float
    regan_threshold: float


class TournamentSummaryResponse(BaseModel):
    player_id: str
    event_id: str
    event_type: str
    games_count: int
    analyzed_move_count: int
    ipr_estimate: float
    pep_score: float
    regan_z_score: float
    regan_threshold: float
    confidence_intervals: dict[str, list[float] | None] = Field(default_factory=dict)
    per_game: list[TournamentGameSummary] = Field(default_factory=list)


class SystemStatusResponse(BaseModel):
    generated_at_utc: str
    app_env: str
    model_version: str
    feature_schema_version: str
    report_schema_version: str
    calibration: dict[str, Any]
    ml_fusion: dict[str, Any]
    maia: dict[str, Any]
    engine: dict[str, Any]
    opening_book: dict[str, Any]
    tablebase: dict[str, Any]
    supabase_configured: bool
    rbac_enabled: bool
    tenant_enforcement_enabled: bool
    lc0_ready: bool
    maia_models_detected: bool
    ml_models_loaded: bool
    analysis_pipeline_operational: bool
    warnings: list[str] = Field(default_factory=list)


class CaseCreateRequest(BaseModel):
    title: str
    event_id: str | None = None
    players: list[str] = Field(default_factory=list)
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: str | None = None
    assigned_to: str | None = None


class CaseStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(opened|under_review|analysis_completed|escalated|closed)$")


class CaseRecord(BaseModel):
    id: str
    created_at: str
    updated_at: str
    status: str
    title: str
    event_id: str | None = None
    players: list[str] = Field(default_factory=list)
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: str | None = None
    assigned_to: str | None = None


class CaseNoteCreateRequest(BaseModel):
    author: str | None = None
    note_type: str | None = None
    structured: dict[str, Any] = Field(default_factory=dict)
    text: str | None = None


class CaseEvidenceCreateRequest(BaseModel):
    evidence_type: str
    label: str | None = None
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseFlagCreateRequest(BaseModel):
    flag_type: str
    severity: str = Field(default="info", pattern="^(info|low|medium|high|critical)$")
    message: str
    metadata: dict[str, Any] = Field(default_factory=dict)


<<<<<<< HEAD
class CaseReviewCreateRequest(BaseModel):
    reviewer_user_id: str | None = None
    action: str = Field(pattern="^(note|request_more_data|recommend_monitoring|recommend_escalation|close_case)$")
    rationale: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class CaseSignoffCreateRequest(BaseModel):
    signer_user_id: str | None = None
    signer_role: str
    decision: str = Field(pattern="^(approved|rejected|returned_for_review)$")
    note: str | None = None


=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
class ReportGenerateRequest(BaseModel):
    case_id: str | None = None
    audit_id: str | None = None
    mode: str = Field(default="arbiter", pattern="^(technical|arbiter|legal)$")
    report_type: str = Field(default="analysis")
    export_format: str = Field(default="json", pattern="^(json|csv|pdf)$")
    use_ai: bool = False
    llm_provider: str | None = Field(default=None, pattern="^(openai|anthropic|none)?$")
<<<<<<< HEAD
    llm_api_url: str | None = None
    llm_api_key: str | None = None
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    llm_model: str | None = None
    pdf_engine: str | None = Field(default=None, pattern="^(auto|weasyprint|minimal)?$")


class OTBIncidentCreateRequest(BaseModel):
    case_id: str | None = None
    event_id: str | None = None
    player_id: str | None = None
    incident_type: str
    severity: str = Field(default="info", pattern="^(info|low|medium|high|critical)$")
    description: str | None = None
    occurred_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OTBIncidentRecord(BaseModel):
    id: str
    case_id: str | None = None
    event_id: str | None = None
    player_id: str | None = None
    incident_type: str
    severity: str
    description: str | None = None
    occurred_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class OTBCameraEventRequest(BaseModel):
    event_id: str | None = None
    case_id: str | None = None
    player_id: str | None = None
    session_id: str | None = None
    camera_id: str | None = None
    storage_mode: str = Field(default="safe", pattern="^(safe|raw)$")
    consent: dict[str, Any] = Field(default_factory=dict)
    events: list[dict[str, Any]] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


class CameraServiceEventPayload(BaseModel):
<<<<<<< HEAD
    model_config = ConfigDict(populate_by_name=True)

=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    event_id: str | None = None
    case_id: str | None = None
    player_id: str | None = None
    session_id: str | None = None
    storage_mode: str = Field(default="safe", pattern="^(safe|raw)$")
    event_id_external: str | None = Field(default=None, alias="eventId")
    event_type: str | None = Field(default=None, alias="eventType")
    timestamp: str | None = None
    tenant_id: str | None = Field(default=None, alias="tenantId")
    device_id: str | None = Field(default=None, alias="deviceId")
    data: dict[str, Any] = Field(default_factory=dict)
    consent: dict[str, Any] = Field(default_factory=dict)

<<<<<<< HEAD
=======
    class Config:
        allow_population_by_field_name = True


>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
class DGTBoardEventRequest(BaseModel):
    event_id: str | None = None
    session_id: str | None = None
    board_serial: str | None = None
    move_uci: str | None = None
    ply: int | None = None
    fen: str | None = None
    clock_ms: int | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ReportRecord(BaseModel):
    id: str
    case_id: str | None = None
    audit_id: str | None = None
    created_at: str
    report_type: str
    mode: str
    format: str
    content: dict[str, Any]


class LiveSessionCreateRequest(BaseModel):
    event_id: str | None = None
    players: list[str] = Field(default_factory=list)


class LiveMoveIngestRequest(BaseModel):
    session_id: str
    ply: int
    move_uci: str
    time_spent: float | None = None
    clock_remaining: float | None = None
    complexity: float | None = None
    engine_match: float | None = None
    maia_prob: float | None = None
    tags: dict[str, Any] = Field(default_factory=dict)


class VisualsRequest(BaseModel):
    game: GameInput
    official_elo: int | None = None


class TournamentDashboardResponse(BaseModel):
    event_id: str | None = None
    players: list[dict[str, Any]] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class PlayerProfileResponse(BaseModel):
    player_id: str
    updated_at: str | None = None
    profile: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)


class PartnerAnalyzeRequest(BaseModel):
    game_id: str
    player_id: str
    player_color: str = Field(default="white", pattern="^(white|black)$")
    pgn: str
    official_elo: int | None = None
    fen_history: list[str] = Field(default_factory=list)
    move_history: list[dict[str, Any]] = Field(default_factory=list)
    mouse_events: list[dict[str, Any]] = Field(default_factory=list)
    click_timing: list[dict[str, Any]] = Field(default_factory=list)
    window_events: dict[str, Any] = Field(default_factory=dict)
    keyboard_events: list[dict[str, Any]] = Field(default_factory=list)
    page_events: list[dict[str, Any]] = Field(default_factory=list)
    touch_events: list[dict[str, Any]] = Field(default_factory=list)
    connection_events: list[dict[str, Any]] = Field(default_factory=list)
    environment: dict[str, Any] = Field(default_factory=dict)
    session: dict[str, Any] = Field(default_factory=dict)
    per_move_summary: list[dict[str, Any]] = Field(default_factory=list)
    camera_events: list[dict[str, Any]] = Field(default_factory=list)
    camera_storage_mode: str = Field(default="safe", pattern="^(safe|raw)$")
    consent: dict[str, Any] = Field(default_factory=dict)
    device_fingerprint: dict[str, Any] = Field(default_factory=dict)


class PartnerKeyCreateRequest(BaseModel):
    partner_name: str
    webhook_url: str | None = None
    rate_limit_per_minute: int = 60


class PartnerWebhookRegisterRequest(BaseModel):
    webhook_url: str


class PartnerSessionCreateRequest(BaseModel):
    game_id: str | None = None
    player_id: str | None = None


<<<<<<< HEAD
class AnalyzePgnBatchRequest(BaseModel):
    event_id: str | None = None
    event_type: str = Field(default="online", pattern="^(online|otb)$")
    pgn_text: str
    tracked_player_name: str | None = None
    tracked_player_id: str | None = None
    default_player_color: str = Field(default="white", pattern="^(white|black)$")
    default_official_elo: int | None = None
    analyze_both_players: bool = False
    high_stakes_event: bool = False
    performance_rating_this_event: float | None = None
    historical: HistoricalProfile = Field(default_factory=HistoricalProfile)
    max_games: int = Field(default=500, ge=1, le=500)


class BatchAnalyzePgnItem(BaseModel):
    player_name: str
    player_id: str
    games_count: int
    source_game_ids: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    official_elo: int
    avg_opponent_official_elo: float | None = None
    audit_id: str
    risk_tier: str
    weighted_risk_score: float
    regan_z_score: float | None = None
    ipr_estimate: float | None = None
    analyzed_move_count: int
    regan_row: dict[str, Any] = Field(default_factory=dict)


class BatchAnalyzePgnResponse(BaseModel):
    event_id: str | None = None
    source_name: str | None = None
    batch_run_id: str | None = None
    players_analyzed: int = 0
    games_parsed: int
    analyses_generated: int
    csv_columns: list[str] = Field(default_factory=list)
    rows: list[BatchAnalyzePgnItem] = Field(default_factory=list)
    failures: list[dict[str, str]] = Field(default_factory=list)


=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
class PartnerKeyRotateResponse(BaseModel):
    id: str
    key: str
    secret: str
    partner_name: str
