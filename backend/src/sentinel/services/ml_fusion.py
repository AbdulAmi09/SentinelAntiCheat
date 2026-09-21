from __future__ import annotations

import math
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from sentinel.config import settings
from sentinel.domain.models import AggregatedFeatures, SignalResult


def _clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _feature_vector(features: AggregatedFeatures, layers: list[SignalResult]) -> np.ndarray:
    by_name = {l.name: l for l in layers}
    vec = np.array(
        [
            float(features.regan_z_score),
            float(features.regan_threshold),
            float(features.engine_match_pct),
            float(features.top3_match_pct),
            float(features.avg_centipawn_loss),
            float(features.accuracy_in_complex_positions),
            float(features.complexity_accuracy_ratio),
            float(features.superhuman_move_rate),
            float(features.rating_adjusted_move_probability),
            float(features.move_quality_uniformity_score),
            float(features.round_anomaly_clustering_score),
            float(features.maia_humanness_score),
            float(features.engine_match_pct - features.maia_humanness_score),
            float(features.avg_engine_gap_cp),
            float(features.avg_position_complexity),
            float(features.avg_engine_rank),
            float(features.hard_best_move_rate),
            float(features.rating_band_index),
            float(features.style_deviation_score),
            float(features.timing_confidence_score),
            float(by_name.get("Layer1_IPR_MoveQuality", SignalResult("", False, 0.0, 0.0)).score),
            float(by_name.get("Layer2_ComplexityAdjusted", SignalResult("", False, 0.0, 0.0)).score),
            float(by_name.get("Layer3_TimeComplexity", SignalResult("", False, 0.0, 0.0)).score),
            float(by_name.get("Layer4_HistoricalBaseline", SignalResult("", False, 0.0, 0.0)).score),
            float(by_name.get("Layer5_BehavioralConsistency", SignalResult("", False, 0.0, 0.0)).score),
            float(features.historical_volatility_score),
            float(features.multi_tournament_anomaly_score),
            float(features.career_growth_curve_score),
        ],
        dtype=float,
    )
    return vec.reshape(1, -1)


@lru_cache(maxsize=2)
def _load_model(path: str) -> Any | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        if p.suffix.lower() == ".json":
            try:
                import xgboost as xgb  # type: ignore

                booster = xgb.Booster()
                booster.load_model(str(p))
                return booster
            except Exception:
                return None
        import joblib  # type: ignore

        return joblib.load(p)
    except Exception:
        try:
            with p.open("rb") as f:
                return pickle.load(f)  # nosec B301 - controlled local artifact path
        except Exception:
            return None


def _predict_primary(model: Any, x: np.ndarray) -> float | None:
    try:
        try:
            import xgboost as xgb  # type: ignore

            if isinstance(model, xgb.Booster):
                dmat = xgb.DMatrix(x)
                pred = model.predict(dmat)
                if pred is not None and len(pred) > 0:
                    value = pred[0]
                    if isinstance(value, (list, tuple, np.ndarray)) and len(value) >= 2:
                        return float(_clip(float(value[1])))
                    return float(_clip(float(value)))
        except Exception:
            pass
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(x)
            if proba is not None and len(proba) > 0 and len(proba[0]) >= 2:
                return float(_clip(float(proba[0][1])))
        if hasattr(model, "predict"):
            pred = model.predict(x)
            if pred is not None and len(pred) > 0:
                return float(_clip(float(pred[0])))
    except Exception:
        return None
    return None


def _predict_secondary(model: Any, x: np.ndarray) -> float | None:
    try:
        if hasattr(model, "score_samples"):
            raw = model.score_samples(x)
            if raw is not None and len(raw) > 0:
                # IsolationForest: lower often more anomalous.
                return float(_clip(_sigmoid(-float(raw[0]))))
        if hasattr(model, "decision_function"):
            raw = model.decision_function(x)
            if raw is not None and len(raw) > 0:
                return float(_clip(_sigmoid(-float(raw[0]))))
        if hasattr(model, "predict"):
            pred = model.predict(x)
            if pred is not None and len(pred) > 0:
                # sklearn IF predict: -1 anomaly, 1 normal.
                return 1.0 if float(pred[0]) < 0 else 0.0
    except Exception:
        return None
    return None


def fused_score(
    features: AggregatedFeatures,
    layers: list[SignalResult],
    heuristic_score: float,
) -> tuple[float, dict[str, float | str | None]]:
    meta: dict[str, float | str | None] = {
        "source": "heuristic_only",
        "heuristic_score": float(heuristic_score),
        "primary_score": None,
        "secondary_score": None,
    }
    if not settings.ml_fusion_enabled:
        return float(_clip(heuristic_score)), meta
    if features.analyzed_move_count < settings.ml_fusion_min_moves:
        meta["source"] = "heuristic_only_low_sample"
        return float(_clip(heuristic_score)), meta

    x = _feature_vector(features, layers)
    primary: float | None = None
    secondary: float | None = None

    if settings.xgboost_model_path:
        primary_model = _load_model(settings.xgboost_model_path)
        if primary_model is not None:
            primary = _predict_primary(primary_model, x)
    if settings.isolation_forest_model_path:
        secondary_model = _load_model(settings.isolation_forest_model_path)
        if secondary_model is not None:
            secondary = _predict_secondary(secondary_model, x)

    meta["primary_score"] = primary
    meta["secondary_score"] = secondary

    components: list[tuple[float, float]] = [(settings.ml_fusion_weight_heuristic, float(_clip(heuristic_score)))]
    if primary is not None:
        components.append((settings.ml_fusion_weight_primary, float(_clip(primary))))
    if secondary is not None:
        components.append((settings.ml_fusion_weight_secondary, float(_clip(secondary))))

    if len(components) == 1:
        meta["source"] = "heuristic_only_no_models"
        return float(_clip(heuristic_score)), meta

    denom = sum(w for w, _ in components)
    fused = sum(w * s for w, s in components) / max(1e-9, denom)
    if primary is not None and secondary is not None:
        meta["source"] = "heuristic_xgb_iforest"
    elif primary is not None:
        meta["source"] = "heuristic_xgb"
    else:
        meta["source"] = "heuristic_iforest"
    return float(_clip(fused)), meta


def _model_status(path: str | None) -> dict[str, Any]:
    if not path:
        return {"path": None, "exists": False, "load_ok": None}
    exists = Path(path).exists()
    load_ok = None
    if exists:
        load_ok = _load_model(path) is not None
    return {"path": path, "exists": exists, "load_ok": load_ok}


def ml_fusion_status() -> dict[str, Any]:
    primary = _model_status(settings.xgboost_model_path)
    secondary = _model_status(settings.isolation_forest_model_path)
    primary_loaded = bool(primary.get("load_ok")) if primary.get("exists") else False
    secondary_loaded = bool(secondary.get("load_ok")) if secondary.get("exists") else False
    return {
        "enabled": settings.ml_fusion_enabled,
        "min_moves": settings.ml_fusion_min_moves,
        "weights": {
            "heuristic": settings.ml_fusion_weight_heuristic,
            "primary": settings.ml_fusion_weight_primary,
            "secondary": settings.ml_fusion_weight_secondary,
        },
        "primary": primary,
        "secondary": secondary,
        "models_present": bool(primary["exists"] or secondary["exists"]),
        "primary_loaded": primary_loaded,
        "secondary_loaded": secondary_loaded,
        "models_loaded": bool(primary_loaded or secondary_loaded),
    }
