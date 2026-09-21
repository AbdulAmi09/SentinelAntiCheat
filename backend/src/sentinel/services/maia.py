from __future__ import annotations

from typing import Any

from sentinel.config import settings
from sentinel.services.maia_policy import maia_models_available

def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _heuristic_humanness(
    observed_match: float,
    expected_human_match: float,
    superhuman_move_rate: float,
    round_anomaly_clustering_score: float,
) -> float:
    divergence = abs(observed_match - expected_human_match)
    return float(
        _clip(
            1.0
            - (0.55 * divergence)
            - (0.25 * superhuman_move_rate)
            - (0.20 * _clip(round_anomaly_clustering_score / 0.4, 0.0, 1.0)),
            0.0,
            1.0,
        )
    )


def score_maia_humanness(
    observed_match: float,
    expected_human_match: float,
    superhuman_move_rate: float,
    round_anomaly_clustering_score: float,
    official_elo: int,
) -> tuple[float, float, str]:
    divergence = float(abs(observed_match - expected_human_match))
    humanness = _heuristic_humanness(
        observed_match=observed_match,
        expected_human_match=expected_human_match,
        superhuman_move_rate=superhuman_move_rate,
        round_anomaly_clustering_score=round_anomaly_clustering_score,
    )
    return divergence, float(_clip(humanness, 0.0, 1.0)), settings.maia_model_version


def maia_status() -> dict[str, Any]:
    models = maia_models_available()
    lc0_path = settings.maia_lc0_path.strip() if isinstance(settings.maia_lc0_path, str) else settings.maia_lc0_path
    return {
        "path": settings.maia_model_path,
        "exists": bool(settings.maia_model_path),
        "load_ok": None,
        "version": settings.maia_model_version,
        "models_dir": models.get("models_dir"),
        "available_buckets": models.get("buckets"),
        "available_count": models.get("count"),
        "lc0_path": lc0_path or None,
    }
