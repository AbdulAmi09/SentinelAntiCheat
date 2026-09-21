from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.signal_layers import evaluate_all_layers


def _request_with_opponents() -> AnalyzeRequest:
    game1 = GameInput(
        game_id="g1",
        opponent_official_elo=2100,
        moves=[
            MoveInput(
                ply=i,
                engine_best="Nf3",
                player_move="Nf3",
                cp_loss=4 if i % 2 else 9,
                top3_match=True,
                complexity_score=7 if i % 2 else 5,
                candidate_moves_within_50cp=2,
                is_opening_book=(i < 8),
                time_spent_seconds=9,
            )
            for i in range(10, 30)
        ],
    )
    game2 = GameInput(
        game_id="g2",
        opponent_official_elo=1700,
        moves=[
            MoveInput(
                ply=i,
                engine_best="Nf3",
                player_move="Nf3" if i % 3 else "Nc3",
                cp_loss=6 if i % 3 else 42,
                top3_match=True,
                complexity_score=6,
                candidate_moves_within_50cp=2,
                is_opening_book=(i < 36),
                time_spent_seconds=10,
            )
            for i in range(30, 50)
        ],
    )
    return AnalyzeRequest(
        player_id="p-phase2",
        event_id="evt-phase2",
        event_type="online",
        official_elo=1800,
        games=[game1, game2],
        historical=HistoricalProfile(games_count=20, avg_acl=45, std_acl=12, avg_ipr=1850, std_ipr=110),
    )


def test_phase2_features_are_computed() -> None:
    req = _request_with_opponents()
    f = compute_features(req)

    assert 0.0 <= f.superhuman_move_rate <= 1.0
    assert f.superhuman_move_rate > 0.0
    assert f.rating_adjusted_move_probability >= 0.0
    assert 0.0 <= f.opening_familiarity_index <= 1.0
    assert f.opponent_strength_correlation is None or -1.0 <= f.opponent_strength_correlation <= 1.0
    assert f.round_anomaly_clustering_score >= 0.0
    assert 0.0 <= f.complex_blunder_rate <= 1.0
    assert isinstance(f.zero_blunder_in_complex_games_flag, bool)
    assert 0.0 <= f.move_quality_uniformity_score <= 1.0


def test_phase2_metrics_influence_layer2_reasons() -> None:
    req = _request_with_opponents()
    f = compute_features(req)
    layers = evaluate_all_layers(f)
    layer2 = [l for l in layers if l.name == "Layer2_ComplexityAdjusted"][0]

    assert layer2.score >= 1.0
    assert any("rating-adjusted" in r.lower() or "high rate" in r.lower() for r in layer2.reasons)


def test_zero_blunder_complex_rule_triggers_layer5_reason() -> None:
    req = _request_with_opponents()
    f = compute_features(req)
    layers = evaluate_all_layers(f)
    layer5 = [l for l in layers if l.name == "Layer5_BehavioralConsistency"][0]

    assert f.zero_blunder_in_complex_games_flag is True
    assert any("zero blunders in complex positions" in r.lower() for r in layer5.reasons)


def test_move_quality_uniformity_feature_is_available() -> None:
    f = compute_features(_request_with_opponents())
    assert 0.0 <= f.move_quality_uniformity_score <= 1.0
