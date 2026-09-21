from __future__ import annotations

from statistics import mean, median

import numpy as np

from sentinel.config import settings
from sentinel.domain.models import AggregatedFeatures
from sentinel.schemas import AnalyzeRequest, MoveInput
from sentinel.services.calibration import regan_acl_params_for_elo
from sentinel.services.maia import score_maia_humanness
from sentinel.services.phase_filter import split_analysis_window, timing_available
from sentinel.services.policy import regan_threshold_for_event
from sentinel.services.regan_metrics import compute_regan_metrics
from sentinel.services.style_fingerprint import style_deviation_score


def _safe_ratio(a: float, b: float) -> float:
    return a / b if b != 0 else 0.0


def _z(value: float | None, avg: float | None, std: float | None) -> float | None:
    if value is None or avg is None or std is None or std == 0:
        return None
    return (value - avg) / std


def _ipr_from_acl(avg_acl: float) -> float:
    # Calibrated monotonic proxy: lower ACL -> higher IPR, bounded to human range.
    return max(100.0, min(3600.0, 3300.0 - (28.0 * avg_acl)))


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _rating_band_index(elo: int) -> int:
    if elo < 1200:
        return 0
    if elo < 1800:
        return 1
    if elo < 2400:
        return 2
    return 3


def _wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    if n <= 0:
        return None
    p = successes / n
    denom = 1.0 + (z * z) / n
    center = (p + (z * z) / (2.0 * n)) / denom
    margin = (z / denom) * np.sqrt((p * (1.0 - p) / n) + ((z * z) / (4.0 * n * n)))
    return float(max(0.0, center - margin)), float(min(1.0, center + margin))


def _mean_ci(values: list[float], z: float = 1.96) -> tuple[float, float] | None:
    n = len(values)
    if n == 0:
        return None
    mu = float(mean(values))
    if n == 1:
        return mu, mu
    std = float(np.std(np.array(values, dtype=float), ddof=1))
    se = std / np.sqrt(n)
    return mu - z * se, mu + z * se


def compute_features(req: AnalyzeRequest) -> AggregatedFeatures:
    behavioral = req.behavioral or {}
    b_copy = int(behavioral.get("copy_paste_events") or 0)
    b_focus = int(behavioral.get("focus_loss_count") or 0)
    b_tab = int(behavioral.get("tab_switch_count") or b_focus)
    b_straight = float(behavioral.get("avg_mouse_path_straightness") or 0.0)
    b_time = float(behavioral.get("avg_move_time_seconds") or 0.0)
    b_mouse = int(behavioral.get("mouse_event_count") or 0)
    b_drag = float(behavioral.get("avg_drag_duration_ms") or 0.0)
    b_dwell = float(behavioral.get("avg_hover_dwell_played_square_ms") or 0.0)
    b_squares = float(behavioral.get("avg_squares_visited") or 0.0)
    b_reaction = float(behavioral.get("avg_reaction_time_ms") or 0.0)
    camera_summary = behavioral.get("camera_summary") if isinstance(behavioral, dict) else {}
    if not isinstance(camera_summary, dict):
        camera_summary = {}
    cam_event_count = int(camera_summary.get("event_count") or 0)
    cam_face_missing = int(camera_summary.get("face_missing_count") or 0)
    cam_multiple_faces = int(camera_summary.get("multiple_faces_count") or 0)
    cam_gaze_away = int(camera_summary.get("gaze_away_count") or 0)
    cam_low_light = int(camera_summary.get("low_light_count") or 0)
    cam_microphone = int(camera_summary.get("microphone_active_count") or 0)
    identity_conf = behavioral.get("identity_confidence") if isinstance(behavioral, dict) else {}
    if not isinstance(identity_conf, dict):
        identity_conf = {}
    identity_shared = bool(identity_conf.get("shared_device"))
    identity_distinct = int(identity_conf.get("distinct_count") or 0)
    identity_seen = int(identity_conf.get("seen_count") or 0)
    all_moves: list[MoveInput] = [m for g in req.games for m in g.moves]
    window, analyzed = split_analysis_window(all_moves)
    if analyzed == 0:
        regan_threshold = regan_threshold_for_event(req.event_type)  # type: ignore[arg-type]
        regan_expected_acl, regan_acl_std = regan_acl_params_for_elo(req.official_elo)
        style_score, style_games = style_deviation_score(req.games)
        return AggregatedFeatures(
            analyzed_move_count=0,
            engine_match_pct=0,
            top3_match_pct=0,
            avg_centipawn_loss=0,
            median_centipawn_loss=0,
            cpl_variance=0,
            ipr_estimate=req.official_elo,
            ipr_vs_official_elo_delta=0,
            ipr_z_score=0,
            regan_z_score=0,
            regan_threshold=regan_threshold,
            regan_expected_acl=regan_expected_acl,
            regan_acl_std=regan_acl_std,
            pep_score=0,
            pep_positions_count=0,
            event_type=req.event_type,
            accuracy_in_complex_positions=0,
            accuracy_in_simple_positions=0,
            complexity_accuracy_ratio=0,
            critical_moment_accuracy=0,
            avg_candidate_moves_in_window=0,
            avg_engine_gap_cp=0,
            avg_position_complexity=0,
            avg_engine_rank=0,
            hard_best_move_rate=0,
            time_complexity_correlation=None,
            fast_engine_move_rate=None,
            think_then_engine_rate=None,
            avg_time_complex_vs_simple=None,
            time_variance_anomaly_score=None,
            time_clustering_anomaly_flag=None,
            break_timing_correlation=None,
            timing_confidence_score=0.0,
            acl_z_score_vs_self=None,
            ipr_z_score_vs_self=None,
            performance_spike_z_score=None,
            move_quality_clustering=0,
            blunder_rate=0,
            inaccuracy_rate=0,
            superhuman_move_rate=0,
            rating_adjusted_move_probability=0,
            opening_familiarity_index=0,
            opponent_strength_correlation=None,
            round_anomaly_clustering_score=0,
            complex_blunder_rate=0,
            zero_blunder_in_complex_games_flag=False,
            move_quality_uniformity_score=0,
            stockfish_maia_divergence=0,
            maia_humanness_score=0,
            maia_personalization_confidence=0,
            maia_model_version=settings.maia_model_version,
            rolling_12m_weighted_acl=float(req.historical.avg_acl or 0.0),
            historical_volatility_score=0.0,
            opponent_pool_adjustment=0.0,
            multi_tournament_anomaly_score=0.0,
            career_growth_curve_score=0.0,
            rating_band_index=_rating_band_index(req.official_elo),
            style_deviation_score=style_score,
            style_baseline_games=style_games,
            games_count_history=req.historical.games_count,
            timing_available=False,
            cold_start=req.historical.games_count < 10,
            behavioral_copy_paste_events=b_copy,
            behavioral_focus_loss_count=b_focus,
            behavioral_tab_switch_count=b_tab,
            behavioral_avg_mouse_path_straightness=b_straight,
            behavioral_avg_move_time_seconds=b_time,
            behavioral_mouse_event_count=b_mouse,
            behavioral_avg_drag_duration_ms=b_drag,
            behavioral_avg_hover_dwell_played_square_ms=b_dwell,
            behavioral_avg_squares_visited=b_squares,
            behavioral_avg_reaction_time_ms=b_reaction,
            camera_event_count=cam_event_count,
            camera_face_missing_count=cam_face_missing,
            camera_multiple_faces_count=cam_multiple_faces,
            camera_gaze_away_count=cam_gaze_away,
            camera_low_light_count=cam_low_light,
            camera_microphone_active_count=cam_microphone,
            identity_shared_device=identity_shared,
            identity_distinct_count=identity_distinct,
            identity_seen_count=identity_seen,
            regan_metrics=None,
            confidence_intervals={},
        )

    engine_best_match = [1 if m.player_move == m.engine_best else 0 for m in window]
    top3_match = [1 if (m.top3_match or m.player_move == m.engine_best) else 0 for m in window]
    cpl = [m.cp_loss for m in window]
    complex_moves = [m for m in window if m.complexity_score >= 3]
    simple_moves = [m for m in window if m.complexity_score <= 1]
    critical = [m for m in window if m.eval_swing_cp >= 100]

    complex_acc = mean([1 if m.player_move == m.engine_best else 0 for m in complex_moves]) if complex_moves else 0.0
    simple_acc = mean([1 if m.player_move == m.engine_best else 0 for m in simple_moves]) if simple_moves else 0.0

    avg_acl = float(mean(cpl))
    ipr = _ipr_from_acl(avg_acl)
    ipr_delta = ipr - req.official_elo
    ipr_z = ipr_delta / 100.0
    regan_expected_acl, regan_acl_std = regan_acl_params_for_elo(req.official_elo)
    regan_z = float((regan_expected_acl - avg_acl) / regan_acl_std)
    regan_threshold = regan_threshold_for_event(req.event_type)  # type: ignore[arg-type]
    equal_positions = [m for m in window if abs(m.best_eval_cp) <= 100.0]
    pep_score = float(mean([m.cp_loss / 100.0 for m in equal_positions])) if equal_positions else float(avg_acl / 100.0)
    # Phase 2: superhuman-like precision in hard positions.
    superhuman_hits = [m for m in window if m.cp_loss <= 8 and m.complexity_score >= 5]
    superhuman_move_rate = float(len(superhuman_hits) / analyzed) if analyzed > 0 else 0.0
    # Phase 2: observed engine-match relative to rating-expected baseline.
    expected_match = _clip(0.22 + (req.official_elo / 4000.0) * 0.48, 0.2, 0.75)
    observed_match = float(mean(engine_best_match))
    rating_adjusted_move_probability = float(_clip(observed_match / max(0.05, expected_match), 0.0, 3.0))
    opening_total = len([m for m in all_moves if m.is_opening_book])
    opening_familiarity_index = float(opening_total / max(1, len(all_moves)))
    complex_blunders = [m for m in complex_moves if m.cp_loss >= 120]
    complex_blunder_rate = float(len(complex_blunders) / max(1, len(complex_moves))) if complex_moves else 0.0
    zero_blunder_in_complex_games_flag = bool(
        len(complex_moves) >= 12 and len(complex_blunders) == 0 and complex_acc >= 0.78
    )

    engine_gaps = [m.best_second_gap_cp for m in window]
    position_complexity = [
        float(m.legal_move_count if m.legal_move_count is not None else m.complexity_score) for m in window
    ]
    engine_ranks = [float(m.engine_rank) for m in window if m.engine_rank is not None]
    avg_engine_gap_cp = float(mean(engine_gaps)) if engine_gaps else 0.0
    avg_position_complexity = float(mean(position_complexity)) if position_complexity else 0.0
    avg_engine_rank = float(mean(engine_ranks)) if engine_ranks else 0.0
    hard_moves = [
        m
        for m in window
        if (m.best_second_gap_cp >= 80 or (m.legal_move_count or 0) >= 18)
    ]
    hard_best = [
        m
        for m in hard_moves
        if (m.engine_rank == 1)
        and (m.maia_probability is not None and m.maia_probability <= 0.2)
    ]
    hard_best_move_rate = float(len(hard_best) / max(1, len(hard_moves))) if hard_moves else 0.0

    has_time = timing_available(window)
    time_corr = None
    fast_engine_rate = None
    think_then_engine = None
    time_complex_simple = None
    time_variance_anomaly_score = None
    time_clustering_anomaly_flag = None
    break_timing_correlation = None
    timing_confidence_score = 0.0

    if has_time:
        pairs = [(m.time_spent_seconds, m.complexity_score) for m in window if m.time_spent_seconds is not None]
        timed_moves = [m for m in window if m.time_spent_seconds is not None]
        timed_values = np.array([float(m.time_spent_seconds or 0.0) for m in timed_moves], dtype=float)
        coverage = float(len(timed_moves) / max(1, analyzed))
        if len(pairs) >= 2:
            times = np.array([p[0] for p in pairs], dtype=float)
            comps = np.array([p[1] for p in pairs], dtype=float)
            time_corr = float(np.corrcoef(times, comps)[0, 1]) if np.std(times) > 0 and np.std(comps) > 0 else 0.0

        if len(timed_values) >= 3:
            mean_time = float(np.mean(timed_values))
            std_time = float(np.std(timed_values, ddof=1))
            expected_std = max(4.0, mean_time * 0.55)
            time_variance_anomaly_score = float(_clip(abs(std_time - expected_std) / expected_std, 0.0, 2.0))
            cv = std_time / max(1e-6, mean_time)
            time_clustering_anomaly_flag = bool(len(timed_values) >= 12 and cv < 0.35)
        else:
            time_variance_anomaly_score = 0.0
            time_clustering_anomaly_flag = False

        if len(timed_values) >= 6:
            threshold = float(np.quantile(timed_values, 0.9))
            break_pairs: list[tuple[float, float]] = []
            for idx in range(1, len(timed_moves)):
                prev_t = timed_moves[idx - 1].time_spent_seconds
                cur_t = timed_moves[idx].time_spent_seconds
                if prev_t is None or cur_t is None:
                    continue
                if float(prev_t) >= threshold:
                    break_pairs.append((float(cur_t), float(timed_moves[idx].complexity_score)))
            if len(break_pairs) >= 2:
                bx = np.array([x[0] for x in break_pairs], dtype=float)
                by = np.array([x[1] for x in break_pairs], dtype=float)
                break_timing_correlation = float(np.corrcoef(bx, by)[0, 1]) if np.std(bx) > 0 and np.std(by) > 0 else 0.0

        fast_complex = [m for m in complex_moves if m.time_spent_seconds is not None and m.time_spent_seconds < 10]
        if complex_moves:
            fast_engine_rate = float(mean([1 if m.player_move == m.engine_best else 0 for m in fast_complex])) if fast_complex else 0.0
            think_then = [m for m in complex_moves if m.time_spent_seconds is not None and m.time_spent_seconds > 90]
            think_then_engine = float(mean([1 if m.player_move == m.engine_best else 0 for m in think_then])) if think_then else 0.0

        complex_times = [m.time_spent_seconds for m in complex_moves if m.time_spent_seconds is not None]
        simple_times = [m.time_spent_seconds for m in simple_moves if m.time_spent_seconds is not None]
        if complex_times and simple_times and mean(simple_times) > 0:
            time_complex_simple = float(mean(complex_times) / mean(simple_times))

        variability = float(np.std(timed_values, ddof=1) / max(1e-6, np.mean(timed_values))) if len(timed_values) > 1 else 0.0
        timing_confidence_score = float(
            _clip((coverage * 0.6) + (_clip(len(timed_values) / 30.0, 0.0, 1.0) * 0.25) + (_clip(variability, 0.0, 1.0) * 0.15), 0.0, 1.0)
        )

    perf_spike = _z(req.performance_rating_this_event, req.historical.avg_perf, req.historical.std_perf)
    opponent_strength_correlation = None
    opp_elo_with_match: list[tuple[float, float]] = []
    for g in req.games:
        if g.opponent_official_elo is None:
            continue
        gw = [m for m in g.moves if not (m.is_opening_book or m.is_tablebase or m.is_forced)]
        if not gw:
            continue
        gmatch = mean([1 if m.player_move == m.engine_best else 0 for m in gw])
        opp_elo_with_match.append((float(g.opponent_official_elo), float(gmatch)))
    if len(opp_elo_with_match) >= 2:
        xs = np.array([x[0] for x in opp_elo_with_match], dtype=float)
        ys = np.array([x[1] for x in opp_elo_with_match], dtype=float)
        if np.std(xs) > 0 and np.std(ys) > 0:
            opponent_strength_correlation = float(np.corrcoef(xs, ys)[0, 1])
        else:
            opponent_strength_correlation = 0.0

    # Phase 2: round-by-round anomaly clustering proxy via per-game anomaly volatility.
    game_anomaly_scores: list[float] = []
    for g in req.games:
        gw = [m for m in g.moves if not (m.is_opening_book or m.is_tablebase or m.is_forced)]
        if not gw:
            continue
        g_acl = mean([m.cp_loss for m in gw])
        g_match = mean([1 if m.player_move == m.engine_best else 0 for m in gw])
        anomaly = (0.55 * g_match) + (0.45 * _clip(1.0 - (g_acl / 120.0), 0.0, 1.0))
        game_anomaly_scores.append(float(anomaly))
    round_anomaly_clustering_score = 0.0
    if len(game_anomaly_scores) >= 2:
        round_anomaly_clustering_score = float(np.std(np.array(game_anomaly_scores, dtype=float), ddof=1))
    # Phase 2 remaining: move-quality distribution uniformity score.
    cpl_std = float(np.std(np.array(cpl, dtype=float), ddof=1)) if len(cpl) > 1 else 0.0
    move_quality_uniformity_score = float(_clip(1.0 - (cpl_std / max(1.0, avg_acl)), 0.0, 1.0))
    # Phase 3: Maia-compatible stack with optional real policy probabilities.
    expected_human_match = _clip(0.18 + (req.official_elo / 4000.0) * 0.42, 0.18, 0.65)
    maia_probs = [m.maia_probability for m in window if m.maia_probability is not None]
    if maia_probs:
        maia_humanness_score = float(_clip(mean(maia_probs), 0.0, 1.0))
        stockfish_maia_divergence = float(abs(maia_humanness_score - expected_human_match))
        maia_model_version = settings.maia_model_version
    else:
        stockfish_maia_divergence, maia_humanness_score, maia_model_version = score_maia_humanness(
            observed_match=observed_match,
            expected_human_match=expected_human_match,
            superhuman_move_rate=superhuman_move_rate,
            round_anomaly_clustering_score=round_anomaly_clustering_score,
            official_elo=req.official_elo,
        )
    maia_personalization_confidence = float(_clip(req.historical.games_count / 80.0, 0.05, 1.0))
    style_score, style_games = style_deviation_score(req.games)
    # Phase 5: historical and longitudinal modeling proxies.
    game_acls: list[float] = []
    for g in req.games:
        gw = [m for m in g.moves if not (m.is_opening_book or m.is_tablebase or m.is_forced)]
        if gw:
            game_acls.append(float(mean([m.cp_loss for m in gw])))
    rolling_12m_weighted_acl = avg_acl
    if game_acls:
        # Recency weighting proxy using game order when explicit dates are unavailable.
        weights = np.arange(1, len(game_acls) + 1, dtype=float)
        rolling_12m_weighted_acl = float(np.average(np.array(game_acls, dtype=float), weights=weights))
    historical_volatility_score = 0.0
    if len(game_acls) >= 2:
        game_acl_std = float(np.std(np.array(game_acls, dtype=float), ddof=1))
        historical_volatility_score = float(_clip(game_acl_std / max(8.0, rolling_12m_weighted_acl), 0.0, 2.0))
    opp_elos = [float(g.opponent_official_elo) for g in req.games if g.opponent_official_elo is not None]
    opponent_pool_adjustment = 0.0
    if opp_elos:
        opponent_pool_adjustment = float(_clip((mean(opp_elos) - req.official_elo) / 400.0, -1.0, 1.0))
    # Uses already-derived per-game anomaly spread as multi-event consistency proxy.
    multi_tournament_anomaly_score = float(_clip(round_anomaly_clustering_score / 0.35, 0.0, 1.5))
    baseline_ipr = req.historical.avg_ipr if req.historical.avg_ipr is not None else float(req.official_elo)
    growth_scale = _clip(req.historical.games_count / 60.0, 0.2, 1.0)
    career_growth_curve_score = float(_clip(((ipr - baseline_ipr) / 220.0) * growth_scale, -2.0, 2.0))

    engine_wins = sum(engine_best_match)
    top3_wins = sum(top3_match)
    acl_ci = _mean_ci(cpl)
    pep_samples = [m.cp_loss / 100.0 for m in equal_positions] if equal_positions else []
    pep_ci = _mean_ci(pep_samples) if pep_samples else None
    regan_ci = None
    ipr_ci = None
    if acl_ci is not None:
        acl_low, acl_high = acl_ci
        ipr_low = _ipr_from_acl(float(acl_high))
        ipr_high = _ipr_from_acl(float(acl_low))
        ipr_ci = (float(min(ipr_low, ipr_high)), float(max(ipr_low, ipr_high)))
        regan_ci = (
            float((regan_expected_acl - acl_high) / regan_acl_std),
            float((regan_expected_acl - acl_low) / regan_acl_std),
        )
    ci_map: dict[str, tuple[float, float] | None] = {
        "ipr_estimate": ipr_ci,
        "engine_match_pct": _wilson_ci(engine_wins, analyzed),
        "top3_match_pct": _wilson_ci(top3_wins, analyzed),
        "avg_centipawn_loss": acl_ci,
        "pep_score": pep_ci,
        "regan_z_score": regan_ci,
    }
    regan_metrics = compute_regan_metrics(all_moves, req.official_elo)

    perf_spike = _z(req.performance_rating_this_event, req.historical.avg_perf, req.historical.std_perf)
    opponent_strength_correlation = None
    opp_elo_with_match: list[tuple[float, float]] = []
    for g in req.games:
        if g.opponent_official_elo is None:
            continue
        gw = [m for m in g.moves if not (m.is_opening_book or m.is_tablebase or m.is_forced)]
        if not gw:
            continue
        gmatch = mean([1 if m.player_move == m.engine_best else 0 for m in gw])
        opp_elo_with_match.append((float(g.opponent_official_elo), float(gmatch)))
    if len(opp_elo_with_match) >= 2:
        xs = np.array([x[0] for x in opp_elo_with_match], dtype=float)
        ys = np.array([x[1] for x in opp_elo_with_match], dtype=float)
        if np.std(xs) > 0 and np.std(ys) > 0:
            opponent_strength_correlation = float(np.corrcoef(xs, ys)[0, 1])
        else:
            opponent_strength_correlation = 0.0

    # Phase 2: round-by-round anomaly clustering proxy via per-game anomaly volatility.
    game_anomaly_scores: list[float] = []
    for g in req.games:
        gw = [m for m in g.moves if not (m.is_opening_book or m.is_tablebase or m.is_forced)]
        if not gw:
            continue
        g_acl = mean([m.cp_loss for m in gw])
        g_match = mean([1 if m.player_move == m.engine_best else 0 for m in gw])
        anomaly = (0.55 * g_match) + (0.45 * _clip(1.0 - (g_acl / 120.0), 0.0, 1.0))
        game_anomaly_scores.append(float(anomaly))
    round_anomaly_clustering_score = 0.0
    if len(game_anomaly_scores) >= 2:
        round_anomaly_clustering_score = float(np.std(np.array(game_anomaly_scores, dtype=float), ddof=1))
    # Phase 2 remaining: move-quality distribution uniformity score.
    cpl_std = float(np.std(np.array(cpl, dtype=float), ddof=1)) if len(cpl) > 1 else 0.0
    move_quality_uniformity_score = float(_clip(1.0 - (cpl_std / max(1.0, avg_acl)), 0.0, 1.0))
    # Phase 3: Maia-compatible stack with optional real policy probabilities.
    expected_human_match = _clip(0.18 + (req.official_elo / 4000.0) * 0.42, 0.18, 0.65)
    maia_probs = [m.maia_probability for m in window if m.maia_probability is not None]
    if maia_probs:
        maia_humanness_score = float(_clip(mean(maia_probs), 0.0, 1.0))
        stockfish_maia_divergence = float(abs(maia_humanness_score - expected_human_match))
        maia_model_version = settings.maia_model_version
    else:
        stockfish_maia_divergence, maia_humanness_score, maia_model_version = score_maia_humanness(
            observed_match=observed_match,
            expected_human_match=expected_human_match,
            superhuman_move_rate=superhuman_move_rate,
            round_anomaly_clustering_score=round_anomaly_clustering_score,
            official_elo=req.official_elo,
        )
    maia_personalization_confidence = float(_clip(req.historical.games_count / 80.0, 0.05, 1.0))
    style_score, style_games = style_deviation_score(req.games)
    # Phase 5: historical and longitudinal modeling proxies.
    game_acls: list[float] = []
    for g in req.games:
        gw = [m for m in g.moves if not (m.is_opening_book or m.is_tablebase or m.is_forced)]
        if gw:
            game_acls.append(float(mean([m.cp_loss for m in gw])))
    rolling_12m_weighted_acl = avg_acl
    if game_acls:
        # Recency weighting proxy using game order when explicit dates are unavailable.
        weights = np.arange(1, len(game_acls) + 1, dtype=float)
        rolling_12m_weighted_acl = float(np.average(np.array(game_acls, dtype=float), weights=weights))
    historical_volatility_score = 0.0
    if len(game_acls) >= 2:
        game_acl_std = float(np.std(np.array(game_acls, dtype=float), ddof=1))
        historical_volatility_score = float(_clip(game_acl_std / max(8.0, rolling_12m_weighted_acl), 0.0, 2.0))
    opp_elos = [float(g.opponent_official_elo) for g in req.games if g.opponent_official_elo is not None]
    opponent_pool_adjustment = 0.0
    if opp_elos:
        opponent_pool_adjustment = float(_clip((mean(opp_elos) - req.official_elo) / 400.0, -1.0, 1.0))
    # Uses already-derived per-game anomaly spread as multi-event consistency proxy.
    multi_tournament_anomaly_score = float(_clip(round_anomaly_clustering_score / 0.35, 0.0, 1.5))
    baseline_ipr = req.historical.avg_ipr if req.historical.avg_ipr is not None else float(req.official_elo)
    growth_scale = _clip(req.historical.games_count / 60.0, 0.2, 1.0)
    career_growth_curve_score = float(_clip(((ipr - baseline_ipr) / 220.0) * growth_scale, -2.0, 2.0))

    engine_wins = sum(engine_best_match)
    top3_wins = sum(top3_match)
    acl_ci = _mean_ci(cpl)
    pep_samples = [m.cp_loss / 100.0 for m in equal_positions] if equal_positions else []
    pep_ci = _mean_ci(pep_samples) if pep_samples else None
    regan_ci = None
    if acl_ci is not None:
        acl_low, acl_high = acl_ci
        regan_ci = (
            float((regan_expected_acl - acl_high) / regan_acl_std),
            float((regan_expected_acl - acl_low) / regan_acl_std),
        )
    ci_map: dict[str, tuple[float, float] | None] = {
        "engine_match_pct": _wilson_ci(engine_wins, analyzed),
        "top3_match_pct": _wilson_ci(top3_wins, analyzed),
        "avg_centipawn_loss": acl_ci,
        "pep_score": pep_ci,
        "regan_z_score": regan_ci,
    }

    return AggregatedFeatures(
        analyzed_move_count=analyzed,
        engine_match_pct=float(mean(engine_best_match)),
        top3_match_pct=float(mean(top3_match)),
        avg_centipawn_loss=avg_acl,
        median_centipawn_loss=float(median(cpl)),
        cpl_variance=float(np.var(cpl)),
        ipr_estimate=ipr,
        ipr_vs_official_elo_delta=ipr_delta,
        ipr_z_score=ipr_z,
        regan_z_score=regan_z,
        regan_threshold=regan_threshold,
        regan_expected_acl=regan_expected_acl,
        regan_acl_std=regan_acl_std,
        pep_score=pep_score,
        pep_positions_count=len(equal_positions),
        event_type=req.event_type,
        accuracy_in_complex_positions=float(complex_acc),
        accuracy_in_simple_positions=float(simple_acc),
        complexity_accuracy_ratio=float(_safe_ratio(complex_acc, simple_acc if simple_acc > 0 else 0.0001)),
        critical_moment_accuracy=float(mean([1 if m.player_move == m.engine_best else 0 for m in critical])) if critical else 0.0,
        avg_candidate_moves_in_window=float(mean([m.candidate_moves_within_50cp for m in window])),
        avg_engine_gap_cp=avg_engine_gap_cp,
        avg_position_complexity=avg_position_complexity,
        avg_engine_rank=avg_engine_rank,
        hard_best_move_rate=hard_best_move_rate,
        time_complexity_correlation=time_corr,
        fast_engine_move_rate=fast_engine_rate,
        think_then_engine_rate=think_then_engine,
        avg_time_complex_vs_simple=time_complex_simple,
        time_variance_anomaly_score=time_variance_anomaly_score,
        time_clustering_anomaly_flag=time_clustering_anomaly_flag,
        break_timing_correlation=break_timing_correlation,
        timing_confidence_score=timing_confidence_score,
        acl_z_score_vs_self=_z(avg_acl, req.historical.avg_acl, req.historical.std_acl),
        ipr_z_score_vs_self=_z(ipr, req.historical.avg_ipr, req.historical.std_ipr),
        performance_spike_z_score=perf_spike,
        move_quality_clustering=float(np.var(cpl) / (avg_acl + 1.0)),
        blunder_rate=float(mean([1 if x >= 120 else 0 for x in cpl])),
        inaccuracy_rate=float(mean([1 if x >= 50 else 0 for x in cpl])),
        superhuman_move_rate=superhuman_move_rate,
        rating_adjusted_move_probability=rating_adjusted_move_probability,
        opening_familiarity_index=opening_familiarity_index,
        opponent_strength_correlation=opponent_strength_correlation,
        round_anomaly_clustering_score=round_anomaly_clustering_score,
        complex_blunder_rate=complex_blunder_rate,
        zero_blunder_in_complex_games_flag=zero_blunder_in_complex_games_flag,
        move_quality_uniformity_score=move_quality_uniformity_score,
        stockfish_maia_divergence=stockfish_maia_divergence,
        maia_humanness_score=maia_humanness_score,
        maia_personalization_confidence=maia_personalization_confidence,
        maia_model_version=maia_model_version,
        rolling_12m_weighted_acl=rolling_12m_weighted_acl,
        historical_volatility_score=historical_volatility_score,
        opponent_pool_adjustment=opponent_pool_adjustment,
        multi_tournament_anomaly_score=multi_tournament_anomaly_score,
        career_growth_curve_score=career_growth_curve_score,
        rating_band_index=_rating_band_index(req.official_elo),
        style_deviation_score=style_score,
        style_baseline_games=style_games,
        games_count_history=req.historical.games_count,
        timing_available=has_time,
        cold_start=req.historical.games_count < 10,
        behavioral_copy_paste_events=b_copy,
        behavioral_focus_loss_count=b_focus,
        behavioral_tab_switch_count=b_tab,
        behavioral_avg_mouse_path_straightness=b_straight,
        behavioral_avg_move_time_seconds=b_time,
        behavioral_mouse_event_count=b_mouse,
        behavioral_avg_drag_duration_ms=b_drag,
        behavioral_avg_hover_dwell_played_square_ms=b_dwell,
        behavioral_avg_squares_visited=b_squares,
        behavioral_avg_reaction_time_ms=b_reaction,
        camera_event_count=cam_event_count,
        camera_face_missing_count=cam_face_missing,
        camera_multiple_faces_count=cam_multiple_faces,
        camera_gaze_away_count=cam_gaze_away,
        camera_low_light_count=cam_low_light,
        camera_microphone_active_count=cam_microphone,
        identity_shared_device=identity_shared,
        identity_distinct_count=identity_distinct,
        identity_seen_count=identity_seen,
        regan_metrics=regan_metrics,
        confidence_intervals=ci_map,
    )
