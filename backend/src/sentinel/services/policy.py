from __future__ import annotations

import math
from typing import Literal

from sentinel.config import settings

EventType = Literal["online", "otb"]


def regan_threshold_for_event(event_type: EventType) -> float:
    if event_type == "otb":
        return max(settings.fide_floor_z_otb, settings.federation_threshold_z_otb)
    return max(settings.fide_floor_z_online, settings.federation_threshold_z_online)


def natural_occurrence_statement(z_score: float, threshold: float) -> str:
    if z_score < threshold:
        return "Within expected variation."

    # One-sided normal tail probability for unusually strong overperformance.
    p = 0.5 * math.erfc(z_score / math.sqrt(2.0))
    if p <= 0:
        return (
            "The observed performance has an estimated probability of natural occurrence of "
            "approximately 1 in 1,000,000+ games among players of similar rating and history."
        )

    n = 1.0 / p
    if n < 10:
        n_display = "10"
    elif n >= 1_000_000:
        n_display = "1,000,000+"
    else:
        exp = int(math.floor(math.log10(n)))
        rounded = int(round(n, -exp))
        n_display = f"{rounded:,}"

    return (
        "The observed performance has an estimated probability of natural occurrence of "
        f"approximately 1 in {n_display} games among players of similar rating and history."
    )


def natural_occurrence_probability(z_score: float, threshold: float) -> float | None:
    if z_score < threshold:
        return None
    p = 0.5 * math.erfc(z_score / math.sqrt(2.0))
    return max(0.0, min(1.0, p))
