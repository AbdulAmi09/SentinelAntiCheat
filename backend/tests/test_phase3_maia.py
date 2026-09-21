from sentinel.config import settings
from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.signal_layers import evaluate_all_layers


def _request_for_maia() -> AnalyzeRequest:
    games = []
    for gidx in range(3):
        games.append(
            GameInput(
                game_id=f"gm-{gidx}",
                opponent_official_elo=1900 - (gidx * 120),
                moves=[
                    MoveInput(
                        ply=i,
                        engine_best="Qh5",
                        player_move="Qh5" if i % 4 else "Qe2",
                        cp_loss=5 if i % 4 else 26,
                        top3_match=True,
                        complexity_score=7,
                        candidate_moves_within_50cp=2,
                        time_spent_seconds=11,
                        is_opening_book=(i < 12),
                    )
                    for i in range(12 + gidx * 20, 32 + gidx * 20)
                ],
            )
        )
    return AnalyzeRequest(
        player_id="p-maia",
        event_id="evt-maia",
        event_type="online",
        official_elo=1850,
        games=games,
        historical=HistoricalProfile(games_count=32, avg_acl=44, std_acl=10, avg_ipr=1880, std_ipr=95),
    )


def test_phase3_maia_metrics_are_exposed() -> None:
    f = compute_features(_request_for_maia())

    assert 0.0 <= f.stockfish_maia_divergence <= 1.0
    assert 0.0 <= f.maia_humanness_score <= 1.0
    assert 0.0 <= f.maia_personalization_confidence <= 1.0
    assert isinstance(f.maia_model_version, str)
    assert f.maia_model_version != ""


def test_phase3_maia_metrics_influence_layers() -> None:
    f = compute_features(_request_for_maia())
    layers = evaluate_all_layers(f)
    l2 = [l for l in layers if l.name == "Layer2_ComplexityAdjusted"][0]

    assert l2.score >= 1.0
    assert isinstance(l2.reasons, list)


def test_phase3_maia_model_hook_when_artifact_is_available() -> None:
    old_version = settings.maia_model_version
    try:
        settings.maia_model_version = "maia-v-test"
        req = _request_for_maia()
        for g in req.games:
            for m in g.moves:
                m.maia_probability = 0.8
        f = compute_features(req)
        assert 0.79 <= f.maia_humanness_score <= 0.81
        assert f.maia_model_version == "maia-v-test"
    finally:
        settings.maia_model_version = old_version
