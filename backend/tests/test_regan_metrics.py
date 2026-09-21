from __future__ import annotations

import pytest

from sentinel.schemas import AnalyzeRequest, GameInput, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.regan_metrics import compute_regan_metrics


def _moves() -> list[MoveInput]:
    moves: list[MoveInput] = []
    for ply in range(12, 22):
        moves.append(
            MoveInput(
                ply=ply,
                engine_best="e2e4",
                player_move="e2e4" if ply % 3 else "d2d4",
                cp_loss=6.0 if ply % 3 else 28.0,
                top3_match=True,
                engine_rank=1 if ply % 3 else 2,
                legal_move_count=8,
                complexity_score=3,
                candidate_moves_within_50cp=2,
                best_second_gap_cp=70,
                best_eval_cp=120,
                played_eval_cp=120 if ply % 3 else 92,
                is_forced=False,
            )
        )
    moves.append(
        MoveInput(
            ply=22,
            engine_best="g1f3",
            player_move="g1f3",
            cp_loss=0.0,
            top3_match=True,
            engine_rank=1,
            legal_move_count=1,
            complexity_score=1,
            candidate_moves_within_50cp=1,
            best_second_gap_cp=0,
            best_eval_cp=15,
            played_eval_cp=15,
            is_forced=True,
        )
    )
    return moves


def test_compute_regan_metrics_adds_expected_fields() -> None:
    metrics = compute_regan_metrics(_moves(), 1800)

    assert metrics is not None
    assert metrics.n_moves == 10
    assert 0.0 <= metrics.s <= 1.0
    assert 0.0 <= metrics.c <= 1.0
    assert metrics.expected_s == pytest.approx(0.277)
    assert metrics.expected_c == pytest.approx(0.396)
    assert metrics.IPR12 >= 0.0


def test_feature_pipeline_exposes_regan_metrics() -> None:
    req = AnalyzeRequest(
        player_id="player-1",
        event_id="event-1",
        official_elo=1800,
        games=[GameInput(game_id="g1", opponent_official_elo=1750, moves=_moves())],
    )

    features = compute_features(req)

    assert features.regan_metrics is not None
    assert features.regan_metrics.n_moves == 10
    assert features.regan_metrics.CombZ == features.regan_metrics.CombZ
