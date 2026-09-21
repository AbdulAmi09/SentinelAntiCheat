from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.risk_engine import classify
from sentinel.services.signal_layers import evaluate_all_layers


def _request_with_times(sparse: bool = False) -> AnalyzeRequest:
    moves: list[MoveInput] = []
    for i in range(20, 60):
        has_time = (i % 4 == 0) if sparse else True
        moves.append(
            MoveInput(
                ply=i,
                engine_best="Nf3",
                player_move="Nf3" if i % 5 else "Nc3",
                cp_loss=9 if i % 5 else 42,
                top3_match=True,
                complexity_score=6 if i % 2 else 4,
                candidate_moves_within_50cp=2,
                is_opening_book=False,
                time_spent_seconds=12 if has_time else None,
            )
        )

    return AnalyzeRequest(
        player_id="p-phase4",
        event_id="evt-phase4",
        event_type="online",
        official_elo=1820,
        games=[GameInput(game_id="g1", moves=moves)],
        historical=HistoricalProfile(games_count=22, avg_acl=48, std_acl=11, avg_ipr=1805, std_ipr=100),
    )


def test_phase4_timing_metrics_are_computed() -> None:
    f = compute_features(_request_with_times())

    assert f.timing_available is True
    assert f.time_variance_anomaly_score is not None
    assert 0.0 <= f.time_variance_anomaly_score <= 2.0
    assert isinstance(f.time_clustering_anomaly_flag, bool)
    assert 0.0 <= f.timing_confidence_score <= 1.0


def test_phase4_timing_metrics_influence_layer3() -> None:
    f = compute_features(_request_with_times())
    layers = evaluate_all_layers(f)
    layer3 = [l for l in layers if l.name == "Layer3_TimeComplexity"][0]

    assert layer3.triggered is True
    assert any("variance" in r.lower() or "clustering" in r.lower() for r in layer3.reasons)


def test_phase4_sparse_clock_coverage_reduces_confidence() -> None:
    rich_features = compute_features(_request_with_times(sparse=False))
    rich_layers = evaluate_all_layers(rich_features)
    _, rich_conf, _, _ = classify(rich_features, rich_layers)

    sparse_features = compute_features(_request_with_times(sparse=True))
    sparse_layers = evaluate_all_layers(sparse_features)
    _, sparse_conf, _, _ = classify(sparse_features, sparse_layers)

    assert sparse_features.timing_available is True
    assert sparse_features.timing_confidence_score < rich_features.timing_confidence_score
    assert sparse_conf < rich_conf
