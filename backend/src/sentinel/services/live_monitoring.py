from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


def compute_live_risk(moves: list[dict[str, Any]]) -> dict[str, Any]:
    if not moves:
        return {"risk_tier": "LOW", "confidence": 0.1, "notes": ["No moves ingested yet."]}

    time_vals = [m.get("time_spent") for m in moves if m.get("time_spent") is not None]
    engine_vals = [m.get("engine_match") for m in moves if m.get("engine_match") is not None]
    maia_vals = [m.get("maia_prob") for m in moves if m.get("maia_prob") is not None]

    time_var = pstdev(time_vals) if len(time_vals) > 1 else 0.0
    engine_avg = mean(engine_vals) if engine_vals else 0.0
    maia_avg = mean(maia_vals) if maia_vals else 0.0

    score = 0.0
    score += min(0.6, engine_avg * 0.5)
    score += min(0.4, maia_avg * 0.4)
    score += min(0.3, max(0.0, 1.0 - time_var / 20.0) * 0.3)

    if score >= 0.7:
        tier = "ELEVATED"
    elif score >= 0.45:
        tier = "MODERATE"
    else:
        tier = "LOW"

    notes = []
    if time_var < 4 and len(time_vals) >= 8:
        notes.append("Uniform timing pattern detected over recent moves.")
    if engine_avg > 0.7:
        notes.append("High engine-alignment rate in recent moves.")
    if maia_avg > 0.7:
        notes.append("High Maia alignment rate in recent moves.")

    return {
        "risk_tier": tier,
        "confidence": round(min(0.95, 0.35 + len(moves) / 40.0), 2),
        "risk_score": round(score, 3),
        "timing_variance": round(time_var, 3),
        "engine_alignment_avg": round(engine_avg, 3),
        "maia_alignment_avg": round(maia_avg, 3),
        "notes": notes,
    }
