from sentinel.config import settings
from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services import ml_fusion
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.risk_engine import classify, classify_with_meta
from sentinel.services.signal_layers import evaluate_all_layers


class _FakePrimaryModel:
    def predict_proba(self, x):  # noqa: ANN001
        return [[0.25, 0.75]]


class _FakeSecondaryModel:
    def score_samples(self, x):  # noqa: ANN001
        return [-0.8]


def _req() -> AnalyzeRequest:
    return AnalyzeRequest(
        player_id="p-phase6",
        event_id="evt-phase6",
        event_type="online",
        official_elo=1820,
        games=[
            GameInput(
                game_id="g1",
                moves=[
                    MoveInput(
                        ply=i,
                        engine_best="Nf3",
                        player_move="Nf3" if i % 5 else "Nc3",
                        cp_loss=8 if i % 5 else 50,
                        top3_match=True,
                        complexity_score=5 if i % 2 else 3,
                        candidate_moves_within_50cp=2,
                        time_spent_seconds=15,
                    )
                    for i in range(18, 70)
                ],
            )
        ],
        historical=HistoricalProfile(games_count=26, avg_acl=48, std_acl=11, avg_ipr=1800, std_ipr=95),
    )


def test_phase6_ml_fusion_fallback_without_models() -> None:
    old = (
        settings.ml_fusion_enabled,
        settings.xgboost_model_path,
        settings.isolation_forest_model_path,
        settings.ml_fusion_min_moves,
    )
    try:
        settings.ml_fusion_enabled = True
        settings.xgboost_model_path = None
        settings.isolation_forest_model_path = None
        settings.ml_fusion_min_moves = 20
        ml_fusion._load_model.cache_clear()

        f = compute_features(_req())
        layers = evaluate_all_layers(f)
        _, _, _, weighted, meta = classify_with_meta(f, layers)
        _, _, _, legacy_weighted = classify(f, layers)

        assert 0.0 <= weighted <= 1.0
        assert meta["source"] == "heuristic_only_no_models"
        assert weighted == legacy_weighted
    finally:
        settings.ml_fusion_enabled, settings.xgboost_model_path, settings.isolation_forest_model_path, settings.ml_fusion_min_moves = old
        if hasattr(ml_fusion._load_model, "cache_clear"):
            ml_fusion._load_model.cache_clear()


def test_phase6_ml_fusion_with_primary_and_secondary(monkeypatch) -> None:
    old = (
        settings.ml_fusion_enabled,
        settings.xgboost_model_path,
        settings.isolation_forest_model_path,
        settings.ml_fusion_min_moves,
    )
    try:
        settings.ml_fusion_enabled = True
        settings.xgboost_model_path = "fake-primary.pkl"
        settings.isolation_forest_model_path = "fake-secondary.pkl"
        settings.ml_fusion_min_moves = 20
        ml_fusion._load_model.cache_clear()

        def _fake_loader(path: str):
            if "primary" in path:
                return _FakePrimaryModel()
            if "secondary" in path:
                return _FakeSecondaryModel()
            return None

        monkeypatch.setattr(ml_fusion, "_load_model", _fake_loader)

        f = compute_features(_req())
        layers = evaluate_all_layers(f)
        _, _, _, weighted, meta = classify_with_meta(f, layers)

        assert meta["source"] == "heuristic_xgb_iforest"
        assert meta["primary_score"] is not None
        assert meta["secondary_score"] is not None
        assert 0.0 <= weighted <= 1.0
        assert meta["heuristic_score"] is not None
        assert abs(weighted - float(meta["heuristic_score"])) > 1e-9
    finally:
        settings.ml_fusion_enabled, settings.xgboost_model_path, settings.isolation_forest_model_path, settings.ml_fusion_min_moves = old
        if hasattr(ml_fusion._load_model, "cache_clear"):
            ml_fusion._load_model.cache_clear()
