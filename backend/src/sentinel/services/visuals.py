from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from sentinel.schemas import GameInput, MoveInput


def _implied_rating(cp_loss: float, complexity: int | None) -> float:
    base = 3000.0 - min(2000.0, cp_loss * 4.0)
    if complexity is not None:
        base += min(200.0, complexity * 2.0)
    return max(800.0, min(3000.0, base))


def _rolling_std(values: list[float], window: int) -> list[float]:
    out: list[float] = []
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        chunk = values[start : idx + 1]
        out.append(float(pstdev(chunk)) if len(chunk) > 1 else 0.0)
    return out


def build_visuals_from_game(
    game: GameInput,
    official_elo: int | None = None,
) -> dict[str, Any]:
    moves: list[MoveInput] = game.moves
    cp_losses = [m.cp_loss for m in moves]
    complexities = [m.complexity_score for m in moves]
    time_spent = [m.time_spent_seconds or 0.0 for m in moves]
    implied = [_implied_rating(m.cp_loss, m.complexity_score) for m in moves]

    move_strength = [
        {"ply": m.ply, "implied_rating": implied[idx]} for idx, m in enumerate(moves)
    ]

    heatmap = []
    window = 10
    for idx in range(0, len(moves), window):
        chunk = moves[idx : idx + window]
        if not chunk:
            continue
        top3 = mean([1.0 if m.top3_match else 0.0 for m in chunk])
        maia_vals = [m.maia_probability for m in chunk if m.maia_probability is not None]
        maia_avg = mean(maia_vals) if maia_vals else 0.0
        cp_avg = mean([m.cp_loss for m in chunk])
        score = (top3 * 0.45) + (maia_avg * 0.35) + (max(0.0, 1.0 - cp_avg / 200.0) * 0.2)
        heatmap.append({"start_ply": chunk[0].ply, "end_ply": chunk[-1].ply, "score": round(score, 4)})

    expected_band = None
    if official_elo:
        expected_band = max(5.0, 60.0 - official_elo / 50.0)
    rolling_std = _rolling_std(cp_losses, window=8)
    consistency = [
        {"ply": m.ply, "variance": rolling_std[idx], "expected_band": expected_band}
        for idx, m in enumerate(moves)
    ]

    engine_vs_maia = []
    for m in moves:
        engine = 1.0 if m.top3_match else 0.0
        maia = m.maia_probability if m.maia_probability is not None else 0.0
        engine_vs_maia.append({"ply": m.ply, "engine_alignment": engine, "maia_alignment": maia})

    timing_corr = []
    for idx, m in enumerate(moves):
        timing_corr.append(
            {
                "ply": m.ply,
                "time_spent": time_spent[idx],
                "complexity_score": complexities[idx],
            }
        )

    return {
        "move_strength": move_strength,
        "suspicion_heatmap": heatmap,
        "player_consistency": consistency,
        "engine_vs_maia": engine_vs_maia,
        "timing_correlation": timing_corr,
    }
