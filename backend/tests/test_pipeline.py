from sentinel.domain.models import RiskTier
from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.evidence_report import build_evidence_report
from sentinel.services.risk_engine import classify, classify_with_meta
from sentinel.services.signal_layers import evaluate_all_layers


def _sample_request() -> AnalyzeRequest:
    return AnalyzeRequest(
        player_id="p1",
        event_id="e1",
        official_elo=1800,
        performance_rating_this_event=2250,
        historical=HistoricalProfile(
            games_count=20,
            avg_acl=48,
            std_acl=10,
            avg_ipr=1780,
            std_ipr=75,
            avg_perf=1790,
            std_perf=90,
        ),
        games=[
            GameInput(
                game_id="g1",
                moves=[
                    MoveInput(
                        ply=i,
                        engine_best="Nf3",
                        player_move="Nf3" if i % 5 else "Nc3",
                        cp_loss=8 if i % 5 else 74,
                        top3_match=True,
                        complexity_score=4 if i % 2 else 1,
                        candidate_moves_within_50cp=3 if i % 2 else 1,
                        best_second_gap_cp=22,
                        eval_swing_cp=130 if i % 4 else 40,
                        is_opening_book=False,
                        is_tablebase=False,
                        is_forced=False,
                        time_spent_seconds=35 if i % 2 else 9,
                    )
                    for i in range(20, 70)
                ],
            )
        ],
    )


def test_pipeline_runs() -> None:
    req = _sample_request()
    f = compute_features(req)
    layers = evaluate_all_layers(f)
    tier, conf, _, weighted = classify(f, layers)

    assert f.analyzed_move_count > 0
    assert 0.0 <= conf <= 1.0
    assert 0.0 <= weighted <= 1.0
    assert tier in {
        RiskTier.LOW,
        RiskTier.MODERATE,
        RiskTier.ELEVATED,
        RiskTier.HIGH_STATISTICAL_ANOMALY,
    }


def test_evidence_report_shape() -> None:
    req = _sample_request()
    f = compute_features(req)
    layers = evaluate_all_layers(f)
    _, _, _, weighted, fusion_meta = classify_with_meta(f, layers)
    report = build_evidence_report(req, f, layers, weighted, fusion_meta)

    assert report["conclusion"]
    assert "engine_match_percentage" in report
    assert "maia_agreement_percentage" in report
    assert "anomaly_score" in report
    assert "centipawn_loss_statistics" in report
    assert "position_difficulty_metrics" in report
    assert "analysis_layers" in report
