from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskTier(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH_STATISTICAL_ANOMALY = "HIGH_STATISTICAL_ANOMALY"


@dataclass
class SignalResult:
    name: str
    triggered: bool
    score: float
    threshold: float
    reasons: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedFeatures:
    analyzed_move_count: int
    engine_match_pct: float
    top3_match_pct: float
    avg_centipawn_loss: float
    median_centipawn_loss: float
    cpl_variance: float
    ipr_estimate: float
    ipr_vs_official_elo_delta: float
    ipr_z_score: float
    regan_z_score: float
    regan_threshold: float
    regan_expected_acl: float
    regan_acl_std: float
    pep_score: float
    pep_positions_count: int
    event_type: str
    accuracy_in_complex_positions: float
    accuracy_in_simple_positions: float
    complexity_accuracy_ratio: float
    critical_moment_accuracy: float
    avg_candidate_moves_in_window: float
    avg_engine_gap_cp: float
    avg_position_complexity: float
    avg_engine_rank: float
    hard_best_move_rate: float
    time_complexity_correlation: float | None
    fast_engine_move_rate: float | None
    think_then_engine_rate: float | None
    avg_time_complex_vs_simple: float | None
    time_variance_anomaly_score: float | None
    time_clustering_anomaly_flag: bool | None
    break_timing_correlation: float | None
    timing_confidence_score: float
    acl_z_score_vs_self: float | None
    ipr_z_score_vs_self: float | None
    performance_spike_z_score: float | None
    move_quality_clustering: float
    blunder_rate: float
    inaccuracy_rate: float
    superhuman_move_rate: float
    rating_adjusted_move_probability: float
    opening_familiarity_index: float
    opponent_strength_correlation: float | None
    round_anomaly_clustering_score: float
    complex_blunder_rate: float
    zero_blunder_in_complex_games_flag: bool
    move_quality_uniformity_score: float
    stockfish_maia_divergence: float
    maia_humanness_score: float
    maia_personalization_confidence: float
    maia_model_version: str
    rolling_12m_weighted_acl: float
    historical_volatility_score: float
    opponent_pool_adjustment: float
    multi_tournament_anomaly_score: float
    career_growth_curve_score: float
    rating_band_index: int
    style_deviation_score: float
    style_baseline_games: int
    games_count_history: int
    timing_available: bool
    cold_start: bool
    behavioral_copy_paste_events: int
    behavioral_focus_loss_count: int
    behavioral_tab_switch_count: int
    behavioral_avg_mouse_path_straightness: float
    behavioral_avg_move_time_seconds: float
    behavioral_mouse_event_count: int
    behavioral_avg_drag_duration_ms: float
    behavioral_avg_hover_dwell_played_square_ms: float
    behavioral_avg_squares_visited: float
    behavioral_avg_reaction_time_ms: float
    camera_event_count: int
    camera_face_missing_count: int
    camera_multiple_faces_count: int
    camera_gaze_away_count: int
    camera_low_light_count: int
    camera_microphone_active_count: int
    identity_shared_device: bool
    identity_distinct_count: int
    identity_seen_count: int
    confidence_intervals: dict[str, tuple[float, float] | None]
