from __future__ import annotations

from statistics import mean

from sentinel.schemas import MoveInput


def included_in_analysis_window(m: MoveInput) -> bool:
    return not (m.is_opening_book or m.is_tablebase or m.is_forced)


def split_analysis_window(moves: list[MoveInput]) -> tuple[list[MoveInput], int]:
    window = [m for m in moves if included_in_analysis_window(m)]
    return window, len(window)


def forced_move_heuristic(best_second_gap_cp: float, threshold_cp: int = 50) -> bool:
    return best_second_gap_cp > threshold_cp


def timing_available(moves: list[MoveInput]) -> bool:
    return any(m.time_spent_seconds is not None for m in moves)


def mean_time(moves: list[MoveInput]) -> float:
    values = [m.time_spent_seconds for m in moves if m.time_spent_seconds is not None]
    return float(mean(values)) if values else 0.0
