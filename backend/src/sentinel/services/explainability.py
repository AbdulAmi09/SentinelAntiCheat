from __future__ import annotations

from typing import Any

from sentinel.domain.models import AggregatedFeatures, SignalResult


def _clip(v: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _norm(v: float, scale: float) -> float:
    if scale == 0:
        return 0.0
    return _clip(v / scale, -1.0, 1.0)


def build_explainability(
    features: AggregatedFeatures,
    layers: list[SignalResult],
    weighted_score: float,
    fusion_meta: dict[str, Any] | None = None,
    top_k: int = 6,
) -> tuple[str, list[dict[str, float | str]]]:
    # Phase 7 scaffold: SHAP-like proxy until production SHAP pipeline is wired.
    fusion_meta = fusion_meta or {}
    contributions = {
        "regan_z_score": _norm(features.regan_z_score - features.regan_threshold, 2.0),
        "complexity_accuracy_ratio": _norm(features.complexity_accuracy_ratio - 1.0, 1.2),
        "superhuman_move_rate": _norm(features.superhuman_move_rate, 0.35),
        "rating_adjusted_move_probability": _norm(features.rating_adjusted_move_probability - 1.0, 1.1),
        "time_variance_anomaly_score": _norm(float(features.time_variance_anomaly_score or 0.0), 1.0),
        "historical_volatility_score": _norm(features.historical_volatility_score, 1.0),
        "multi_tournament_anomaly_score": _norm(features.multi_tournament_anomaly_score, 1.0),
        "career_growth_curve_score": _norm(features.career_growth_curve_score, 1.25),
        "maia_humanness_score": _norm(0.5 - features.maia_humanness_score, 0.5),
        "fused_risk_score": _norm(weighted_score - 0.5, 0.5),
    }
    if fusion_meta.get("primary_score") is not None:
        contributions["ml_primary_score"] = _norm(float(fusion_meta["primary_score"]) - 0.5, 0.5)
    if fusion_meta.get("secondary_score") is not None:
        contributions["ml_secondary_score"] = _norm(float(fusion_meta["secondary_score"]) - 0.5, 0.5)

    ranked = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)[:top_k]
    items: list[dict[str, float | str]] = []
    for feat, val in ranked:
        items.append(
            {
                "feature": feat,
                "contribution": round(float(val), 4),
                "direction": "increases_risk" if val >= 0 else "decreases_risk",
            }
        )

    return "shap_proxy_v1", items
