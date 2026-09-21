from __future__ import annotations

import re

from sentinel.config import settings
from sentinel.main import tournament_summary
from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.policy import natural_occurrence_statement, regan_threshold_for_event


def _make_game(game_id: str, start_ply: int) -> GameInput:
    return GameInput(
        game_id=game_id,
        moves=[
            MoveInput(
                ply=i,
                engine_best="Nf3",
                player_move="Nf3" if i % 4 else "Nc3",
                cp_loss=10 if i % 4 else 68,
                top3_match=True,
                complexity_score=4 if i % 2 else 1,
                candidate_moves_within_50cp=3 if i % 2 else 1,
                best_second_gap_cp=20,
                eval_swing_cp=120 if i % 3 else 30,
                best_eval_cp=15,
                played_eval_cp=-10,
                is_opening_book=False,
                is_tablebase=False,
                is_forced=False,
                time_spent_seconds=30 if i % 2 else 11,
            )
            for i in range(start_ply, start_ply + 24)
        ],
    )


def _sample_request(event_type: str = "online") -> AnalyzeRequest:
    return AnalyzeRequest(
        player_id="p1",
        event_id="evt-1",
        event_type=event_type,
        official_elo=1850,
        performance_rating_this_event=2210,
        historical=HistoricalProfile(
            games_count=40,
            avg_acl=48,
            std_acl=9,
            avg_ipr=1810,
            std_ipr=90,
            avg_perf=1820,
            std_perf=95,
        ),
        games=[_make_game("g1", 20), _make_game("g2", 44)],
    )


def test_event_type_threshold_routing_online_and_otb() -> None:
    online = compute_features(_sample_request("online"))
    otb = compute_features(_sample_request("otb"))

    assert online.regan_threshold == 4.25
    assert otb.regan_threshold == 5.0


def test_fide_floor_enforcement() -> None:
    old_vals = {
        "fide_floor_z_online": settings.fide_floor_z_online,
        "fide_floor_z_otb": settings.fide_floor_z_otb,
        "federation_threshold_z_online": settings.federation_threshold_z_online,
        "federation_threshold_z_otb": settings.federation_threshold_z_otb,
    }
    try:
        settings.fide_floor_z_online = 4.25
        settings.fide_floor_z_otb = 5.0
        settings.federation_threshold_z_online = 3.2
        settings.federation_threshold_z_otb = 4.1

        assert regan_threshold_for_event("online") == 4.25
        assert regan_threshold_for_event("otb") == 5.0

        settings.federation_threshold_z_online = 4.8
        settings.federation_threshold_z_otb = 5.6
        assert regan_threshold_for_event("online") == 4.8
        assert regan_threshold_for_event("otb") == 5.6
    finally:
        for key, value in old_vals.items():
            setattr(settings, key, value)


def test_odds_wording_boundaries_and_exact_phrase() -> None:
    assert natural_occurrence_statement(3.0, 4.25) == "Within expected variation."

    min_display = natural_occurrence_statement(0.1, 0.0)
    assert "approximately 1 in 10 games" in min_display

    capped = natural_occurrence_statement(9.0, 4.25)
    assert "approximately 1 in 1,000,000+ games" in capped

    pattern = (
        r"^The observed performance has an estimated probability of natural occurrence "
        r"of approximately 1 in [0-9,\+]+ games among players of similar rating and history\.$"
    )
    assert re.match(pattern, capped)


def test_confidence_intervals_presence_and_shape() -> None:
    features = compute_features(_sample_request("online"))
    ci = features.confidence_intervals

    for key in ["engine_match_pct", "top3_match_pct", "avg_centipawn_loss", "pep_score", "regan_z_score"]:
        assert key in ci
        bounds = ci[key]
        assert bounds is None or (len(bounds) == 2 and bounds[0] <= bounds[1])


def test_tournament_summary_consistency() -> None:
    req = _sample_request("online")
    summary = tournament_summary(req)

    assert summary.event_type == "online"
    assert summary.games_count == len(req.games)
    assert len(summary.per_game) == len(req.games)
    assert summary.regan_threshold == 4.25

    per_game_moves = sum(item.analyzed_move_count for item in summary.per_game)
    assert summary.analyzed_move_count == per_game_moves

    assert isinstance(summary.confidence_intervals, dict)
