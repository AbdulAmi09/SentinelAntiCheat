from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.explainability import build_explainability
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.risk_engine import classify_with_meta
from sentinel.services.signal_layers import evaluate_all_layers


def _request() -> AnalyzeRequest:
    return AnalyzeRequest(
        player_id="p-phase7",
        event_id="evt-phase7",
        event_type="online",
        official_elo=1900,
        games=[
            GameInput(
                game_id="g1",
                opponent_official_elo=2050,
                moves=[
                    MoveInput(
                        ply=i,
                        engine_best="Nf3",
                        player_move="Nf3" if i % 4 else "Nc3",
                        cp_loss=7 if i % 4 else 44,
                        top3_match=True,
                        complexity_score=6 if i % 2 else 4,
                        candidate_moves_within_50cp=2,
                        time_spent_seconds=12,
                    )
                    for i in range(20, 68)
                ],
            )
        ],
        historical=HistoricalProfile(games_count=30, avg_acl=47, std_acl=11, avg_ipr=1840, std_ipr=92),
    )


def test_phase7_explainability_returns_ranked_items() -> None:
    f = compute_features(_request())
    layers = evaluate_all_layers(f)
    _, _, _, weighted, fusion_meta = classify_with_meta(f, layers)
    method, items = build_explainability(f, layers, weighted, fusion_meta)

    assert method == "shap_proxy_v1"
    assert len(items) > 0
    assert len(items) <= 6
    assert "feature" in items[0]
    assert "contribution" in items[0]
    assert "direction" in items[0]
