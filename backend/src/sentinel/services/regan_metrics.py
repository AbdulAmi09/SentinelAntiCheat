from __future__ import annotations

from dataclasses import asdict
from math import exp, sqrt

from sentinel.domain.models import ReganMetrics
from sentinel.schemas import MoveInput


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _win_prob(cp: float) -> float:
    return 1.0 / (1.0 + exp(-cp / 400.0))


def _weight_triplet(official_elo: int) -> tuple[float, float, float]:
    if official_elo < 1500:
        return 0.25, 0.30, 0.45
    if official_elo < 2000:
        return 0.30, 0.35, 0.35
    return 0.35, 0.40, 0.25


def compute_regan_metrics(moves: list[MoveInput], official_elo: int) -> ReganMetrics | None:
    eligible = [move for move in moves if move.ply >= 12 and not move.is_forced]
    n_moves = len(eligible)
    if n_moves == 0:
        return None

    s = sum(1 for move in eligible if move.player_move == move.engine_best) / n_moves
    c = sum(1 for move in eligible if move.played_eval_cp >= move.best_eval_cp) / n_moves
    avg_cp_loss = sum(float(move.cp_loss) for move in eligible) / n_moves

    expected_s = 0.007 + (0.00015 * official_elo)
    expected_c = 0.18 + (0.00012 * official_elo)
    expected_avg_loss = max(10.0, 120.0 - (0.03 * official_elo))

    se_s = sqrt(max(expected_s * (1.0 - expected_s), 1e-9) / n_moves)
    se_c = sqrt(max(expected_c * (1.0 - expected_c), 1e-9) / n_moves)
    se_asd = max(expected_avg_loss / sqrt(n_moves), 1e-9)

    mmz = (s - expected_s) / se_s
    evz = (c - expected_c) / se_c
    asdz = (expected_avg_loss - avg_cp_loss) / se_asd

    w_mmz, w_evz, w_asdz = _weight_triplet(official_elo)
    comb_z = (w_mmz * mmz) + (w_evz * evz) + (w_asdz * asdz)

    ipr12 = _clip((s - 0.007) / 0.00015, 0.0, 3500.0)

    wp_losses = [_win_prob(float(move.best_eval_cp)) - _win_prob(float(move.played_eval_cp)) for move in eligible]
    expected_wp_loss = max(0.001, 0.04 - (0.000012 * official_elo))
    se_wp = max(expected_wp_loss / sqrt(n_moves), 1e-9)
    elwz = ((sum(wp_losses) / n_moves) - expected_wp_loss) / se_wp

    ipr_variance = (3500.0**2) / n_moves
    two_sigma = 2.0 * sqrt(ipr_variance)

    return ReganMetrics(
        s=s,
        c=c,
        MMZ=mmz,
        EVZ=evz,
        ASDZ=asdz,
        CombZ=comb_z,
        IPR12=ipr12,
        ELWZ=elwz,
        two_sigma=two_sigma,
        n_moves=n_moves,
        expected_s=expected_s,
        expected_c=expected_c,
    )


def regan_metrics_to_dict(metrics: ReganMetrics | None) -> dict | None:
    if metrics is None:
        return None
    return asdict(metrics)
