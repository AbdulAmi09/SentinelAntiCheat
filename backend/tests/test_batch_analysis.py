from __future__ import annotations

import chess.pgn

from sentinel.main import _normalize_pgn_request
from sentinel.schemas import AnalyzePgnBatchRequest, AnalyzePgnRequest, GameInput, MoveInput
from sentinel.services.batch_analysis import REGAN_CSV_COLUMNS, build_batch_targets, build_regan_row, regan_rows_to_csv


def _game_with_headers() -> chess.pgn.Game:
    game = chess.pgn.Game()
    game.headers["Event"] = "Rapid Open"
    game.headers["Site"] = "Lagos"
    game.headers["White"] = "Alice"
    game.headers["Black"] = "Bob"
    game.headers["WhiteElo"] = "1820"
    game.headers["BlackElo"] = "1765"
    return game


def test_build_batch_targets_uses_header_elos_and_both_players() -> None:
    req = AnalyzePgnBatchRequest(
        event_id="fed-ng::rapid-open",
        pgn_text="dummy",
        analyze_both_players=True,
    )
    targets, failures = build_batch_targets([_game_with_headers()], req)

    assert failures == []
    assert len(targets) == 2
    assert targets[0].official_elo == 1820
    assert targets[0].games[0].opponent_official_elo == 1765
    assert targets[1].official_elo == 1765
    assert targets[1].games[0].opponent_official_elo == 1820


def test_build_batch_targets_aggregates_games_by_player() -> None:
    game_one = _game_with_headers()
    game_two = _game_with_headers()
    game_two.headers["Black"] = "Carol"
    game_two.headers["BlackElo"] = "1900"

    req = AnalyzePgnBatchRequest(
        event_id="fed-ng::rapid-open",
        pgn_text="dummy",
        tracked_player_name="Alice",
    )
    targets, failures = build_batch_targets([game_one, game_two], req)

    assert failures == []
    assert len(targets) == 1
    assert targets[0].player_name == "Alice"
    assert len(targets[0].games) == 2


def test_build_regan_row_maps_current_feature_fields() -> None:
    target = build_batch_targets(
        [_game_with_headers()],
        AnalyzePgnBatchRequest(event_id="fed-ng::rapid-open", pgn_text="dummy"),
    )[0][0]
    req_payload = {"official_elo": 1820}
    response_payload = {
        "ipr_estimate": 1975.0,
        "regan_z_score": 4.8,
        "maia_humanness_score": 0.21,
        "analyzed_move_count": 38,
        "confidence_intervals": {"ipr_estimate": [1910.0, 2040.0]},
        "regan_metrics": {
            "s": 0.31,
            "c": 0.44,
            "MMZ": 1.17,
            "EVZ": 0.82,
            "ASDZ": 0.56,
            "CombZ": 0.88,
            "IPR12": 2020.0,
            "ELWZ": 0.41,
            "two_sigma": 140.0,
            "n_moves": 38,
            "expected_s": 0.28,
            "expected_c": 0.40,
        },
        "superhuman_move_rate": 0.37,
        "rating_adjusted_move_probability": 1.42,
        "engine_match_pct": 0.61,
        "complexity_accuracy_ratio": 1.18,
        "pep_score": 0.14,
        "multi_tournament_anomaly_score": 0.55,
        "historical_volatility_score": 0.41,
    }

    row = build_regan_row(req_payload=req_payload, response_payload=response_payload, target=target)
    assert row["Name"] == "Alice"
    assert row["Rating"] == 1820
    assert row["ChallFaced"] == 1765
    assert row["2sigma"] == 140.0
    assert row["PredZ"] == 1.16
    assert row["CombZ+"] == 0.88
    assert row["IPR12"] == 2020.0
    assert row["s"] == 0.31
    assert row["c"] == 0.44
    assert row["MMZ"] == 1.17
    assert row["EVZ"] == 0.82
    assert row["ASDZ"] == 0.56
    assert row["ELWZ"] == 0.41
    assert row["sOfIPR"] == 0.31
    assert row["cOfIPR"] == 0.4224
    assert row["ProxyIPR12"] == 1975.0
    assert row["ProxyCombZ"] == 4.8
    assert row["Proxy2sigma"] == 65.0
    assert row["ProxyS"] == 0.37
    assert row["ProxyC"] == 0.61
    assert row["ProxyMMZ"] == 1.26
    assert row["ProxyEVZ"] == 0.66
    assert row["ProxyASDZ"] == 0.72
    assert row["ProxyELWZ"] == 1.44

    csv_text = regan_rows_to_csv([row])
    assert csv_text.splitlines()[0].split(",") == REGAN_CSV_COLUMNS


def test_normalize_pgn_request_infers_official_elo(monkeypatch) -> None:
    game = _game_with_headers()

    class _Ctx:
        def close(self) -> None:
            return None

    monkeypatch.setattr("sentinel.main.parse_pgn_games", lambda _text: [game])
    monkeypatch.setattr("sentinel.main.create_engine_context", lambda _elo: _Ctx())
    monkeypatch.setattr(
        "sentinel.main.game_to_inputs",
        lambda game, game_id, player_color, ctx: GameInput(  # noqa: ARG005
            game_id=game_id,
            opponent_official_elo=1765,
            moves=[
                MoveInput(
                    ply=1,
                    engine_best="e2e4",
                    player_move="e2e4",
                    cp_loss=0.0,
                    complexity_score=2,
                    candidate_moves_within_50cp=1,
                )
            ],
        ),
    )

    normalized, parsed_games, official_elo = _normalize_pgn_request(
        AnalyzePgnRequest(
            player_id="alice",
            event_id="fed-ng::rapid-open",
            player_color="white",
            pgn_text="dummy",
        )
    )

    assert official_elo == 1820
    assert normalized.official_elo == 1820
    assert parsed_games[0].opponent_official_elo == 1765
