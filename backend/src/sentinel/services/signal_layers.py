from __future__ import annotations

from sentinel.domain.models import AggregatedFeatures, SignalResult


def layer_1_ipr(f: AggregatedFeatures) -> SignalResult:
    reasons = []
    threshold = f.regan_threshold
    triggered = f.regan_z_score >= threshold
    if triggered:
        reasons.append(f"Regan-compatible Z exceeds threshold for {f.event_type} play")
    if f.top3_match_pct > 0.85:
        reasons.append("Top-3 engine match unusually high")
    return SignalResult(
        name="Layer1_IPR_MoveQuality",
        triggered=triggered,
        score=f.regan_z_score,
        threshold=threshold,
        reasons=reasons,
    )


def layer_2_complexity(f: AggregatedFeatures) -> SignalResult:
    score = max(
        f.complexity_accuracy_ratio,
        f.rating_adjusted_move_probability,
        1.0 + (f.round_anomaly_clustering_score * 2.0),
        1.0 + (f.stockfish_maia_divergence * 2.0),
    )
    triggered = (
        (f.complexity_accuracy_ratio > 1.0 and f.accuracy_in_complex_positions > 0.7)
        or f.superhuman_move_rate >= 0.2
        or f.rating_adjusted_move_probability >= 1.35
        or f.round_anomaly_clustering_score >= 0.18
        or f.stockfish_maia_divergence >= 0.16
    )
    reasons = []
    if f.complexity_accuracy_ratio > 1.0:
        reasons.append("Accuracy in complex positions exceeds simple positions")
    if f.critical_moment_accuracy > 0.75:
        reasons.append("Critical moment accuracy is elevated")
    if f.superhuman_move_rate >= 0.2:
        reasons.append("High rate of low-CPL play in high-complexity positions")
    if f.rating_adjusted_move_probability >= 1.35:
        reasons.append("Engine-match level materially exceeds rating-adjusted expectation")
    if f.opponent_strength_correlation is not None and f.opponent_strength_correlation < -0.2:
        reasons.append("Stronger-anomaly pattern against weaker opposition detected")
    if f.round_anomaly_clustering_score >= 0.18:
        reasons.append("Round-by-round anomaly clustering observed")
    if f.stockfish_maia_divergence >= 0.16:
        reasons.append("Stockfish-vs-Maia divergence indicates atypical human likeness profile")
    return SignalResult(
        name="Layer2_ComplexityAdjusted",
        triggered=triggered,
        score=score,
        threshold=1.0,
        reasons=reasons,
    )


def layer_3_timing(f: AggregatedFeatures) -> SignalResult:
    if not f.timing_available:
        return SignalResult(
            name="Layer3_TimeComplexity",
            triggered=False,
            score=0.0,
            threshold=0.3,
            reasons=["Clock data absent; layer excluded"],
        )

    corr = f.time_complexity_correlation if f.time_complexity_correlation is not None else 0.0
    fast = f.fast_engine_move_rate if f.fast_engine_move_rate is not None else 0.0
    ratio = f.avg_time_complex_vs_simple if f.avg_time_complex_vs_simple is not None else 0.0
    variance_anomaly = f.time_variance_anomaly_score if f.time_variance_anomaly_score is not None else 0.0
    break_corr = f.break_timing_correlation if f.break_timing_correlation is not None else 0.0

    triggered = (
        corr < 0.1
        or fast > 0.6
        or ratio < 1.4
        or variance_anomaly >= 0.75
        or bool(f.time_clustering_anomaly_flag)
        or break_corr < 0.05
    )
    reasons = []
    if corr < 0.1:
        reasons.append("Weak time-vs-complexity correlation")
    if fast > 0.6:
        reasons.append("High rate of fast engine-like moves in complex positions")
    if ratio < 1.4:
        reasons.append("Complex positions not receiving expected extra think time")
    if variance_anomaly >= 0.75:
        reasons.append("Move-time variance is anomalous versus expected event rhythm")
    if f.time_clustering_anomaly_flag:
        reasons.append("Move-time clustering anomaly detected")
    if f.break_timing_correlation is not None and break_corr < 0.05:
        reasons.append("Post-break move timing weakly tracks position complexity")

    return SignalResult(
        name="Layer3_TimeComplexity",
        triggered=triggered,
        score=max(1.0 - corr, variance_anomaly),
        threshold=0.7,
        reasons=reasons,
    )


def layer_4_historical(f: AggregatedFeatures) -> SignalResult:
    score = max(
        abs(f.acl_z_score_vs_self or 0.0),
        abs(f.ipr_z_score_vs_self or 0.0),
        abs(f.performance_spike_z_score or 0.0),
        abs(f.career_growth_curve_score),
        f.historical_volatility_score,
        f.multi_tournament_anomaly_score,
    )
    triggered = score >= 3.0 or f.multi_tournament_anomaly_score >= 1.0 or abs(f.career_growth_curve_score) >= 1.25
    reasons = []
    if f.cold_start:
        reasons.append("Cold start profile (<10 games); historical confidence reduced")
    if abs(f.career_growth_curve_score) >= 1.25:
        reasons.append("Career trajectory deviation is elevated versus historical baseline")
    if f.historical_volatility_score >= 0.7:
        reasons.append("Historical performance volatility is elevated")
    if f.multi_tournament_anomaly_score >= 1.0:
        reasons.append("Cross-game anomaly spread indicates multi-event instability")
    if triggered and not reasons:
        reasons.append("Performance significantly deviates from player baseline")

    return SignalResult(
        name="Layer4_HistoricalBaseline",
        triggered=triggered,
        score=score,
        threshold=3.0,
        reasons=reasons,
    )


def layer_5_behavioral(f: AggregatedFeatures) -> SignalResult:
    score = (1.0 - f.blunder_rate) + (1.0 - f.inaccuracy_rate) + (1.0 if f.zero_blunder_in_complex_games_flag else 0.0)
    triggered = (
        (f.blunder_rate < 0.01 and f.inaccuracy_rate < 0.08 and f.move_quality_clustering < 0.2)
        or f.zero_blunder_in_complex_games_flag
        or (f.move_quality_uniformity_score >= 0.85 and f.avg_centipawn_loss <= 22)
        or (f.maia_humanness_score <= 0.35 and f.maia_personalization_confidence >= 0.4)
    )
    reasons = []
    if triggered:
        reasons.append("Near-zero blunder/inaccuracy profile in analyzed complex window")
    if f.zero_blunder_in_complex_games_flag:
        reasons.append("Zero blunders in complex positions despite broad analysis window")
    if f.move_quality_uniformity_score >= 0.85 and f.avg_centipawn_loss <= 22:
        reasons.append("Move-quality distribution appears unusually uniform for achieved accuracy")
    if f.maia_humanness_score <= 0.35:
        reasons.append("Low Maia humanness score under personalized profile")

    return SignalResult(
        name="Layer5_BehavioralConsistency",
        triggered=triggered,
        score=score,
        threshold=1.8,
        reasons=reasons,
    )


def layer_6_online_behavioral(f: AggregatedFeatures) -> SignalResult:
    if (
        f.behavioral_copy_paste_events == 0
        and f.behavioral_focus_loss_count == 0
        and f.behavioral_mouse_event_count == 0
    ):
        return SignalResult(
            name="Layer6_OnlineBehavior",
            triggered=False,
            score=0.0,
            threshold=0.6,
            reasons=["No online behavioral telemetry provided"],
        )

    score = 0.0
    reasons = []
    if f.behavioral_copy_paste_events > 0:
        score += 0.4
        reasons.append("Copy/paste events detected during play")
    if f.behavioral_focus_loss_count >= 2:
        score += 0.2
        reasons.append("Repeated focus loss or tab switching observed")
    if f.behavioral_avg_mouse_path_straightness >= 0.92:
        score += 0.2
        reasons.append("Mouse paths appear unusually straight for multiple moves")
    if f.behavioral_avg_drag_duration_ms and f.behavioral_avg_drag_duration_ms < 120:
        score += 0.1
        reasons.append("Drag durations are unusually short on average")
    if f.behavioral_avg_hover_dwell_played_square_ms and f.behavioral_avg_hover_dwell_played_square_ms < 80:
        score += 0.1
        reasons.append("Minimal hover dwell on played square across moves")
    if f.behavioral_avg_move_time_seconds and f.behavioral_avg_move_time_seconds < 6:
        score += 0.1
        reasons.append("Average move time is unusually fast")

    triggered = score >= 0.6
    return SignalResult(
        name="Layer6_OnlineBehavior",
        triggered=triggered,
        score=score,
        threshold=0.6,
        reasons=reasons,
    )


def layer_7_environmental_identity(f: AggregatedFeatures) -> SignalResult:
    if f.camera_event_count == 0 and not f.identity_shared_device:
        return SignalResult(
            name="Layer7_EnvironmentalIdentity",
            triggered=False,
            score=0.0,
            threshold=0.5,
            reasons=["No environmental or identity telemetry provided"],
        )

    score = 0.0
    reasons: list[str] = []
    if f.camera_face_missing_count >= 2:
        score += 0.2
        reasons.append("Repeated face-missing events detected")
    if f.camera_multiple_faces_count >= 1:
        score += 0.2
        reasons.append("Multiple faces detected during monitoring")
    if f.camera_gaze_away_count >= 3:
        score += 0.2
        reasons.append("Repeated gaze-away events detected")
    if f.camera_low_light_count >= 2:
        score += 0.1
        reasons.append("Low-light conditions repeatedly detected")
    if f.identity_shared_device:
        score += 0.2
        reasons.append("Device fingerprint seen across multiple players")
    if f.identity_distinct_count >= 3:
        score += 0.1
        reasons.append("Device fingerprint associated with multiple player IDs")

    triggered = score >= 0.5
    return SignalResult(
        name="Layer7_EnvironmentalIdentity",
        triggered=triggered,
        score=score,
        threshold=0.5,
        reasons=reasons,
    )


def evaluate_all_layers(f: AggregatedFeatures) -> list[SignalResult]:
    return [
        layer_1_ipr(f),
        layer_2_complexity(f),
        layer_3_timing(f),
        layer_4_historical(f),
        layer_5_behavioral(f),
        layer_6_online_behavioral(f),
        layer_7_environmental_identity(f),
    ]
