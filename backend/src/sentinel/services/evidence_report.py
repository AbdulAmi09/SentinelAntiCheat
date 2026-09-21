from __future__ import annotations

from statistics import mean, median
from typing import Any

import numpy as np

from sentinel.domain.models import AggregatedFeatures, SignalResult
from sentinel.schemas import AnalyzeRequest
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.phase_filter import split_analysis_window
from sentinel.services.signal_layers import evaluate_all_layers
from sentinel.services import risk_engine


def _safe_mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _safe_median(values: list[float]) -> float:
    return float(median(values)) if values else 0.0


def build_evidence_report(
    req: AnalyzeRequest,
    features: AggregatedFeatures,
    layers: list[SignalResult],
    weighted_score: float,
    fusion_meta: dict[str, float | str | None],
) -> dict[str, Any]:
    all_moves = [m for g in req.games for m in g.moves]
    window, analyzed = split_analysis_window(all_moves)
    cpl = [m.cp_loss for m in window]
    maia_probs = [m.maia_probability for m in window if m.maia_probability is not None]

    maia_agreement = float(mean(maia_probs)) if maia_probs else None
    maia_probabilities_used = bool(maia_probs)

    anomaly_score: float | None = None
    if fusion_meta.get("primary_score") is not None:
        anomaly_score = float(fusion_meta["primary_score"])  # type: ignore[arg-type]
    elif fusion_meta.get("secondary_score") is not None:
        anomaly_score = float(fusion_meta["secondary_score"])  # type: ignore[arg-type]
    else:
        anomaly_score = float(weighted_score)

    triggered = len([l for l in layers if l.triggered])
    if weighted_score >= 0.56 or triggered >= 2:
        conclusion = "Statistical deviations detected relative to expected human play. Arbiter review recommended."
    else:
        conclusion = "Within expected variation."

    notes: list[str] = []
    if not maia_probabilities_used:
        notes.append("Maia probabilities unavailable; Maia metrics derived from heuristics")
    if analyzed < 15:
        notes.append("Small analysis window; confidence reduced")
    if not features.timing_available:
        notes.append("Clock data absent; timing layer excluded")

    centipawn_loss_statistics = {
        "avg": float(features.avg_centipawn_loss),
        "median": float(features.median_centipawn_loss),
        "variance": float(features.cpl_variance),
        "min": float(min(cpl)) if cpl else 0.0,
        "max": float(max(cpl)) if cpl else 0.0,
    }

    position_difficulty_metrics = {
        "avg_candidate_moves": float(features.avg_candidate_moves_in_window),
        "complexity_accuracy_ratio": float(features.complexity_accuracy_ratio),
        "accuracy_in_complex_positions": float(features.accuracy_in_complex_positions),
        "critical_moment_accuracy": float(features.critical_moment_accuracy),
        "avg_engine_gap_cp": float(features.avg_engine_gap_cp),
        "avg_position_complexity": float(features.avg_position_complexity),
        "avg_engine_rank": float(features.avg_engine_rank),
        "hard_best_move_rate": float(features.hard_best_move_rate),
        "analysis_window_moves": int(features.analyzed_move_count),
    }

    engine_agreement = {
        "engine_match_percentage": float(features.engine_match_pct),
        "engine_top3_match_percentage": float(features.top3_match_pct),
        "avg_centipawn_loss": float(features.avg_centipawn_loss),
        "engine_maia_disagreement": float(features.engine_match_pct - features.maia_humanness_score),
    }

    maia_human_style = {
        "maia_agreement_percentage": maia_agreement,
        "maia_humanness_score": float(features.maia_humanness_score),
        "stockfish_maia_divergence": float(features.stockfish_maia_divergence),
        "maia_model_version": features.maia_model_version,
        "probabilities_used": maia_probabilities_used,
    }

    ml_anomaly = {
        "anomaly_score": anomaly_score,
        "ml_primary_score": fusion_meta.get("primary_score"),
        "ml_secondary_score": fusion_meta.get("secondary_score"),
        "ml_fusion_source": str(fusion_meta.get("source") or "heuristic_only"),
    }

    analysis_layers = [
        {"name": "engine_agreement", "status": "ok", "metrics": engine_agreement},
        {
            "name": "maia_human_style",
            "status": "ok" if maia_probabilities_used else "heuristic_only",
            "metrics": maia_human_style,
        },
        {
            "name": "ml_anomaly_detection",
            "status": "ok" if fusion_meta.get("source") != "heuristic_only_no_models" else "unavailable",
            "metrics": ml_anomaly,
        },
    ]

    signal_payload = [
        {
            "name": l.name,
            "triggered": l.triggered,
            "score": float(l.score),
            "threshold": float(l.threshold),
            "reasons": l.reasons,
        }
        for l in layers
    ]

    per_game_scores: list[float] = []
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
        glayers = evaluate_all_layers(fg)
        per_game_scores.append(float(risk_engine._weighted_score(fg, glayers)))

    player_anomaly_trend = 0.0
    player_anomaly_rolling_avg = float(mean(per_game_scores[-3:])) if per_game_scores else 0.0
    player_anomaly_spike_count = 0
    if len(per_game_scores) >= 2:
        xs = np.arange(len(per_game_scores), dtype=float)
        ys = np.array(per_game_scores, dtype=float)
        if np.std(xs) > 0:
            player_anomaly_trend = float(np.polyfit(xs, ys, 1)[0])
        spike_runs = 0
        current = 0
        for score in per_game_scores:
            if score >= 0.75:
                current += 1
                spike_runs = max(spike_runs, current)
            else:
                current = 0
        player_anomaly_spike_count = spike_runs

    style_context = {
        "style_deviation_score": float(features.style_deviation_score),
        "style_baseline_games": int(features.style_baseline_games),
    }

    behavioral_metrics = {
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
    }

    environmental_metrics = {}
    if isinstance(req.behavioral, dict):
        env = req.behavioral.get("environment")
        if isinstance(env, dict):
            environmental_metrics = env
        camera_summary = req.behavioral.get("camera_summary")
        if isinstance(camera_summary, dict):
            environmental_metrics = {**environmental_metrics, "camera_summary": camera_summary}

    identity_confidence = {}
    if isinstance(req.behavioral, dict):
        identity = req.behavioral.get("identity_confidence")
        if isinstance(identity, dict):
            identity_confidence = identity

    return {
        "conclusion": conclusion,
        "engine_match_percentage": float(features.engine_match_pct),
        "maia_agreement_percentage": maia_agreement,
        "engine_maia_disagreement": float(features.engine_match_pct - features.maia_humanness_score),
        "rating_band_index": int(features.rating_band_index),
        "anomaly_score": anomaly_score,
        "anomaly_source": str(fusion_meta.get("source") or "heuristic_only"),
        "centipawn_loss_statistics": centipawn_loss_statistics,
        "position_difficulty_metrics": position_difficulty_metrics,
        "analysis_layers": analysis_layers,
        "signals": signal_payload,
        "player_anomaly_scores": per_game_scores,
        "player_anomaly_trend": player_anomaly_trend,
        "player_anomaly_rolling_average": player_anomaly_rolling_avg,
        "player_anomaly_spike_count": player_anomaly_spike_count,
        "style_fingerprint": style_context,
        "behavioral_metrics": behavioral_metrics,
        "environmental_metrics": environmental_metrics,
        "identity_confidence": identity_confidence,
        "notes": notes,
    }
