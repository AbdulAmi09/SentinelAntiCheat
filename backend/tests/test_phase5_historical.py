from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.signal_layers import evaluate_all_layers


def _phase5_request() -> AnalyzeRequest:
    games: list[GameInput] = []
    for gidx in range(4):
        moves: list[MoveInput] = []
        for i in range(20 + (gidx * 30), 40 + (gidx * 30)):
            moves.append(
                MoveInput(
                    ply=i,
                    engine_best="Nf3",
                    player_move="Nf3" if i % 6 else "Nc3",
                    cp_loss=8 + (gidx * 6) + (0 if i % 6 else 26),
                    top3_match=True,
                    complexity_score=5 if i % 2 else 3,
                    candidate_moves_within_50cp=2,
                    is_opening_book=False,
                    time_spent_seconds=14 + (gidx % 2),
                )
            )
        games.append(
            GameInput(
                game_id=f"g{gidx+1}",
                opponent_official_elo=1700 + (gidx * 120),
                moves=moves,
            )
        )

    return AnalyzeRequest(
        player_id="p-phase5",
        event_id="evt-phase5",
        event_type="online",
        official_elo=1850,
        games=games,
        historical=HistoricalProfile(
            games_count=36,
            avg_acl=52,
            std_acl=10,
            avg_ipr=1700,
            std_ipr=90,
            avg_perf=1750,
            std_perf=85,
        ),
    )


def test_phase5_historical_metrics_are_computed() -> None:
    f = compute_features(_phase5_request())

    assert f.rolling_12m_weighted_acl > 0.0
    assert 0.0 <= f.historical_volatility_score <= 2.0
    assert -1.0 <= f.opponent_pool_adjustment <= 1.0
    assert 0.0 <= f.multi_tournament_anomaly_score <= 1.5
    assert -2.0 <= f.career_growth_curve_score <= 2.0


def test_phase5_historical_metrics_influence_layer4() -> None:
    f = compute_features(_phase5_request())
    layers = evaluate_all_layers(f)
    layer4 = [l for l in layers if l.name == "Layer4_HistoricalBaseline"][0]

    assert layer4.triggered is True
    assert any(
        "career trajectory" in reason.lower() or "volatility" in reason.lower() or "cross-game anomaly" in reason.lower()
        for reason in layer4.reasons
    )
