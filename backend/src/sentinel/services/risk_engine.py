from __future__ import annotations

from sentinel.config import settings
from sentinel.domain.models import AggregatedFeatures, RiskTier, SignalResult
from sentinel.services.ml_fusion import fused_score


def _clip(v: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, v))


def _confidence(features: AggregatedFeatures, triggered: int, weighted_score: float) -> float:
    base = min(1.0, features.analyzed_move_count / 80.0)
    trigger_boost = min(0.35, triggered * 0.08)
    weighted_boost = min(0.25, weighted_score * 0.25)
    if features.cold_start:
        base *= 0.9
    if not features.timing_available:
        base *= 0.88
    else:
        # Partial/sparse clock coverage reduces confidence even when timing is present.
        timing_factor = 0.8 + (0.2 * max(0.0, min(1.0, features.timing_confidence_score)))
        base *= timing_factor
    return round(max(0.05, min(0.99, base + trigger_boost + weighted_boost)), 3)


def _weighted_score(features: AggregatedFeatures, layers: list[SignalResult]) -> float:
    by_name = {l.name: l for l in layers}

    l1 = _clip((by_name["Layer1_IPR_MoveQuality"].score - 2.0) / 2.5)
    l2_ratio = by_name["Layer2_ComplexityAdjusted"].score
    l2 = _clip((l2_ratio - 1.0) / 1.6)
    l2 = _clip(
        (0.45 * l2)
        + (0.25 * features.accuracy_in_complex_positions)
        + (0.2 * _clip(features.superhuman_move_rate / 0.4))
        + (0.1 * _clip((features.rating_adjusted_move_probability - 1.0) / 1.2))
    )
    l2 = _clip(l2 + (0.08 * _clip(features.stockfish_maia_divergence / 0.3)))
    l3 = _clip(by_name["Layer3_TimeComplexity"].score / 1.4) if features.timing_available else 0.25
    l4 = _clip(by_name["Layer4_HistoricalBaseline"].score / 4.0)
    l5 = _clip((2.0 - features.blunder_rate - features.inaccuracy_rate) / 2.0)
    if features.zero_blunder_in_complex_games_flag:
        l5 = _clip(l5 + 0.18)
    l5 = _clip(
        l5
        + (0.1 * _clip((features.move_quality_uniformity_score - 0.7) / 0.3))
        + (0.12 * _clip((0.5 - features.maia_humanness_score) / 0.5))
    )

    l6 = _clip(by_name.get("Layer6_OnlineBehavior", SignalResult("", False, 0.0, 0.0)).score)
    l7 = _clip(by_name.get("Layer7_EnvironmentalIdentity", SignalResult("", False, 0.0, 0.0)).score)
    w1, w2, w3, w4, w5, w6, w7 = 0.25, 0.3, 0.15, 0.13, 0.07, 0.06, 0.04
    if not features.timing_available:
        # Reallocate timing weight to objective move-quality layers.
        w1 += 0.07
        w2 += 0.06
        w3 = 0.0
    total = (l1 * w1) + (l2 * w2) + (l3 * w3) + (l4 * w4) + (l5 * w5) + (l6 * w6) + (l7 * w7)
    return round(_clip(total), 4)


def classify_with_meta(
    features: AggregatedFeatures,
    layers: list[SignalResult],
) -> tuple[RiskTier, float, list[str], float, dict[str, float | str | None]]:
    triggered = [x for x in layers if x.triggered]
    trigger_count = len(triggered)
    explanation: list[str] = []
    heuristic_score = _weighted_score(features, layers)
    weighted_score, fusion_meta = fused_score(features, layers, heuristic_score)
    by_name = {l.name: l for l in layers}

    if features.analyzed_move_count < 15:
        explanation.append("Small analysis window; confidence reduced")

    tier = RiskTier.LOW
    if trigger_count >= settings.min_elevated_triggers:
        severe_cut = features.regan_threshold + 0.5
        severe = any(x.name == "Layer1_IPR_MoveQuality" and x.score >= severe_cut for x in triggered)
        if severe and trigger_count >= 4:
            tier = RiskTier.HIGH_STATISTICAL_ANOMALY
            explanation.append("Multiple independent layers and severe IPR anomaly")
        else:
            tier = RiskTier.ELEVATED
            explanation.append("At least three independent anomaly layers exceeded thresholds")
    elif trigger_count >= 2:
        tier = RiskTier.MODERATE
        explanation.append("Multiple weak-to-moderate signals observed")

    # Weighted override path prevents rigid-gate blind spots when a severe layer dominates.
    if weighted_score >= 0.78:
        tier = RiskTier.HIGH_STATISTICAL_ANOMALY
        explanation.append("Weighted fusion override: aggregate anomaly score is severe")
    elif weighted_score >= 0.56 and tier == RiskTier.LOW:
        tier = RiskTier.MODERATE
        explanation.append("Weighted fusion override: elevated aggregate anomaly despite sparse triggers")

    layer2_severe = (
        by_name["Layer2_ComplexityAdjusted"].score >= 2.5
        and features.accuracy_in_complex_positions >= 0.85
        and features.analyzed_move_count >= 25
    )
    if layer2_severe and tier in {RiskTier.LOW, RiskTier.MODERATE}:
        tier = RiskTier.ELEVATED
        explanation.append("Layer 2 severe override: anomalous complex-position accuracy")

    layer1_severe = by_name["Layer1_IPR_MoveQuality"].score >= (features.regan_threshold + 0.5)
    if layer1_severe and (by_name["Layer2_ComplexityAdjusted"].triggered or weighted_score >= 0.7):
        tier = RiskTier.HIGH_STATISTICAL_ANOMALY
        explanation.append("Layer 1 severe override with corroboration")

    if features.cold_start:
        explanation.append("Cold-start profile: detection active, confidence adjusted for sparse history")
    if not features.timing_available:
        explanation.append("Clock data absent: timing layer unavailable, move-quality layers weighted more heavily")

    if tier == RiskTier.HIGH_STATISTICAL_ANOMALY:
        explanation.append("Human arbiter review required before action")

    explanation.append(f"ML fusion source: {fusion_meta.get('source')}")
    conf = _confidence(features, trigger_count, weighted_score)
    return tier, conf, explanation, weighted_score, fusion_meta


def classify(features: AggregatedFeatures, layers: list[SignalResult]) -> tuple[RiskTier, float, list[str], float]:
    tier, conf, explanation, weighted_score, _ = classify_with_meta(features, layers)
    return tier, conf, explanation, weighted_score
