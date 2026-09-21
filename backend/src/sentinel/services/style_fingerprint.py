from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Any

import numpy as np

from sentinel.schemas import GameInput, MoveInput
from sentinel.services.phase_filter import split_analysis_window


@dataclass
class StyleProfile:
    means: dict[str, float]
    stds: dict[str, float]
    games_count: int


def _safe_mean(values: list[float]) -> float:
    return float(mean(values)) if values else 0.0


def _game_style_metrics(game: GameInput) -> dict[str, float] | None:
    window, analyzed = split_analysis_window(game.moves)
    if analyzed == 0:
        return None

    engine_match = _safe_mean([1.0 if m.player_move == m.engine_best else 0.0 for m in window])
    cp_losses = [m.cp_loss for m in window]
    blunder_rate = _safe_mean([1.0 if m.cp_loss >= 120 else 0.0 for m in window])
    critical = [m for m in window if m.eval_swing_cp >= 100]
    tactical_accuracy = _safe_mean([1.0 if m.player_move == m.engine_best else 0.0 for m in critical]) if critical else 0.0
    eval_volatility = float(np.std(np.array(cp_losses, dtype=float), ddof=1)) if len(cp_losses) > 1 else 0.0
    maia_probs = [m.maia_probability for m in window if m.maia_probability is not None]
    maia_likelihood = _safe_mean(maia_probs) if maia_probs else 0.0
    opening_ratio = _safe_mean([1.0 if m.is_opening_book else 0.0 for m in window])
    opening_diversity = float(max(0.0, min(1.0, 1.0 - opening_ratio)))

    return {
        "avg_centipawn_loss": _safe_mean(cp_losses),
        "engine_match_rate": engine_match,
        "tactical_move_ratio": tactical_accuracy,
        "evaluation_volatility": eval_volatility,
        "maia_likelihood": maia_likelihood,
        "blunder_rate": blunder_rate,
        "opening_diversity": opening_diversity,
    }


def build_style_profile(games: list[GameInput], max_games: int = 50) -> StyleProfile | None:
    if not games:
        return None
    sample = games[-max_games:] if max_games > 0 else games
    metrics: dict[str, list[float]] = {}
    count = 0
    for g in sample:
        vals = _game_style_metrics(g)
        if vals is None:
            continue
        count += 1
        for k, v in vals.items():
            metrics.setdefault(k, []).append(float(v))

    if count == 0:
        return None

    means = {k: float(mean(v)) for k, v in metrics.items()}
    stds = {}
    for k, v in metrics.items():
        stds[k] = float(np.std(np.array(v, dtype=float), ddof=1)) if len(v) > 1 else 0.0
    return StyleProfile(means=means, stds=stds, games_count=count)


def style_deviation_score(games: list[GameInput], max_games: int = 50) -> tuple[float, int]:
    if len(games) < 2:
        return 0.0, 0
    baseline = games[:-1]
    current = games[-1]
    profile = build_style_profile(baseline, max_games=max_games)
    if profile is None:
        return 0.0, 0
    current_metrics = _game_style_metrics(current)
    if current_metrics is None:
        return 0.0, profile.games_count

    zs: list[float] = []
    for key, mean_val in profile.means.items():
        std_val = profile.stds.get(key, 0.0)
        if std_val <= 0:
            continue
        cur_val = current_metrics.get(key, mean_val)
        zs.append((cur_val - mean_val) / std_val)
    if not zs:
        return 0.0, profile.games_count
    score = float(np.sqrt(np.mean(np.square(np.array(zs, dtype=float)))))
    return score, profile.games_count
