from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

import chess.pgn

from sentinel.config import settings
from sentinel.schemas import AnalyzePgnBatchRequest


REGAN_CSV_COLUMNS = [
    "Name",
    "Rating",
    "Rating Used",
    "IPR12",
    "CombZ",
    "PredZ",
    "#turns",
    "wtfactor",
    "IPR diff",
    "2sigma",
    "ChallFaced",
    "s",
    "c",
    "MMZ",
    "EVZ",
    "ASDZ",
    "ELWZ",
    "Engine",
    "Weights",
    "T2Z",
    "T3Z",
    "T3thr50Z",
    "sOfIPR",
    "cOfIPR",
    "CombZ+",
    "Pred+",
    "ProxyIPR12",
    "ProxyCombZ",
    "Proxy2sigma",
    "ProxyS",
    "ProxyC",
    "ProxyMMZ",
    "ProxyEVZ",
    "ProxyASDZ",
    "ProxyELWZ",
]

_NON_WORD_RE = re.compile(r"[^a-zA-Z0-9]+")


@dataclass
class BatchAnalysisGame:
    game: chess.pgn.Game
    game_id: str
    player_color: str
    opponent_player_id: str
    opponent_player_name: str
    official_elo: int
    opponent_official_elo: int | None


@dataclass
class BatchAnalysisTarget:
    event_id: str
    player_id: str
    player_name: str
    official_elo: int
    games: list[BatchAnalysisGame] = field(default_factory=list)


def _slug(value: str | None, fallback: str) -> str:
    cleaned = _NON_WORD_RE.sub("-", (value or "").strip().lower()).strip("-")
    return cleaned or fallback


def _compact_name(value: str | None, fallback: str) -> str:
    cleaned = _NON_WORD_RE.sub("", (value or "").strip())
    return cleaned or fallback


def _parse_elo(value: str | None) -> int | None:
    cleaned = (value or "").strip()
    if not cleaned or cleaned in {"?", "-", "0"}:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def _player_header_id(name: str | None, fallback_prefix: str, index: int) -> str:
    return _slug(name, f"{fallback_prefix}-{index}")


def _event_id(default_event_id: str | None, game: chess.pgn.Game, index: int) -> str:
    if default_event_id:
        return default_event_id
    header_event = game.headers.get("Event")
    header_site = game.headers.get("Site")
    return _slug(f"{header_event or 'batch'}-{header_site or index}", f"batch-event-{index}")


def _select_colors(req: AnalyzePgnBatchRequest, game: chess.pgn.Game) -> list[str]:
    white_name = (game.headers.get("White") or "").strip().lower()
    black_name = (game.headers.get("Black") or "").strip().lower()
    tracked_name = (req.tracked_player_name or "").strip().lower()

    if req.analyze_both_players:
        return ["white", "black"]
    if tracked_name and tracked_name == white_name:
        return ["white"]
    if tracked_name and tracked_name == black_name:
        return ["black"]
    return [req.default_player_color]


def _player_side_data(
    *,
    game: chess.pgn.Game,
    player_color: str,
    index: int,
    tracked_player_id: str | None,
    default_official_elo: int | None,
) -> tuple[str, str, int, str, str, int | None] | None:
    if player_color == "white":
        player_name = (game.headers.get("White") or "").strip()
        opponent_name = (game.headers.get("Black") or "").strip()
        official_elo = _parse_elo(game.headers.get("WhiteElo"))
        opponent_elo = _parse_elo(game.headers.get("BlackElo"))
    else:
        player_name = (game.headers.get("Black") or "").strip()
        opponent_name = (game.headers.get("White") or "").strip()
        official_elo = _parse_elo(game.headers.get("BlackElo"))
        opponent_elo = _parse_elo(game.headers.get("WhiteElo"))

    resolved_elo = official_elo if official_elo is not None else default_official_elo
    if resolved_elo is None:
        return None

    fallback_name = f"Player{index}"
    player_id = tracked_player_id or _player_header_id(player_name, "player", index)
    player_display_name = player_name or fallback_name
    opponent_player_id = _player_header_id(opponent_name, "opponent", index)
    opponent_display_name = opponent_name or f"Opponent{index}"
    return (
        player_id,
        player_display_name,
        int(resolved_elo),
        opponent_player_id,
        opponent_display_name,
        opponent_elo,
    )


def _dominant_rating(values: list[int], fallback: int) -> int:
    if not values:
        return fallback
    most_common = Counter(values).most_common(1)[0][0]
    return int(most_common)


def build_batch_targets(
    games: list[chess.pgn.Game],
    req: AnalyzePgnBatchRequest,
) -> tuple[list[BatchAnalysisTarget], list[dict[str, str]]]:
    targets_by_player: dict[str, BatchAnalysisTarget] = {}
    rating_history: dict[str, list[int]] = {}
    failures: list[dict[str, str]] = []

    for index, game in enumerate(games[: req.max_games], start=1):
        event_id = _event_id(req.event_id, game, index)
        for color in _select_colors(req, game):
            side_data = _player_side_data(
                game=game,
                player_color=color,
                index=index,
                tracked_player_id=req.tracked_player_id if not req.analyze_both_players else None,
                default_official_elo=req.default_official_elo,
            )
            if side_data is None:
                failures.append(
                    {
                        "game_index": str(index),
                        "player_color": color,
                        "reason": "Unable to resolve official Elo from PGN headers or default_official_elo",
                    }
                )
                continue

            player_id, player_name, official_elo, opponent_id, opponent_name, opponent_elo = side_data
            target = targets_by_player.get(player_id)
            if target is None:
                target = BatchAnalysisTarget(
                    event_id=event_id,
                    player_id=player_id,
                    player_name=player_name,
                    official_elo=official_elo,
                )
                targets_by_player[player_id] = target
                rating_history[player_id] = []
            rating_history[player_id].append(official_elo)
            target.games.append(
                BatchAnalysisGame(
                    game=game,
                    game_id=f"{event_id}:{player_id}:pgn-{index}",
                    player_color=color,
                    opponent_player_id=opponent_id,
                    opponent_player_name=opponent_name,
                    official_elo=official_elo,
                    opponent_official_elo=opponent_elo,
                )
            )

    targets = list(targets_by_player.values())
    for target in targets:
        rating_values = rating_history.get(target.player_id, [])
        target.official_elo = _dominant_rating(rating_values, target.official_elo)
    targets.sort(key=lambda item: item.player_name.lower())
    return targets, failures


def build_regan_row(
    *,
    req_payload: dict[str, Any],
    response_payload: dict[str, Any],
    target: BatchAnalysisTarget,
) -> dict[str, Any]:
    regan_metrics = response_payload.get("regan_metrics") or {}
    confidence_intervals = response_payload.get("confidence_intervals") or {}
    ipr_ci = confidence_intervals.get("ipr_estimate") or confidence_intervals.get("ipr")
    rating_used = int(req_payload.get("official_elo") or target.official_elo)
    opponent_elos = [g.opponent_official_elo for g in target.games if g.opponent_official_elo is not None]
    challenged_faced = round(mean(opponent_elos), 1) if opponent_elos else None

    s_value = float(regan_metrics.get("s") or 0.0)
    c_value = float(regan_metrics.get("c") or 0.0)
    mmz = round(float(regan_metrics.get("MMZ") or 0.0), 2)
    evz = round(float(regan_metrics.get("EVZ") or 0.0), 2)
    asdz = round(float(regan_metrics.get("ASDZ") or 0.0), 2)
    comb_z = round(float(regan_metrics.get("CombZ") or 0.0), 2)
    ipr12 = float(regan_metrics.get("IPR12")) if regan_metrics.get("IPR12") is not None else response_payload.get("ipr_estimate")
    ipr_value = float(ipr12) if isinstance(ipr12, (int, float)) else None
    two_sigma = float(regan_metrics.get("two_sigma")) if regan_metrics.get("two_sigma") is not None else None
    if two_sigma is None and isinstance(ipr_ci, list) and len(ipr_ci) == 2:
        two_sigma = abs(float(ipr_ci[1]) - float(ipr_ci[0])) / 2.0
    elwz = round(float(regan_metrics.get("ELWZ") or 0.0), 2)
    maia_humanness = response_payload.get("maia_humanness_score")
    t2z = round(float(response_payload.get("multi_tournament_anomaly_score") or 0.0), 2)
    t3z = round(float(response_payload.get("historical_volatility_score") or 0.0), 2)

    pred_z = None if maia_humanness is None else round((0.5 - float(maia_humanness)) * 4.0, 2)
    ipr_diff = None if ipr_value is None else ipr_value - float(rating_used)

    proxy_ipr = response_payload.get("ipr_estimate")
    proxy_ipr_value = float(proxy_ipr) if isinstance(proxy_ipr, (int, float)) else None
    proxy_engine_match = float(response_payload.get("engine_match_pct") or 0.0)
    proxy_rating_adjusted = float(response_payload.get("rating_adjusted_move_probability") or 0.0)
    proxy_complexity_ratio = float(response_payload.get("complexity_accuracy_ratio") or 0.0)
    proxy_pep_score = float(response_payload.get("pep_score") or 0.0)
    proxy_superhuman_rate = float(response_payload.get("superhuman_move_rate") or 0.0)
    proxy_mmz = round((proxy_rating_adjusted - 1.0) * 3.0, 2)
    proxy_evz = round((proxy_engine_match - 0.5) * 6.0, 2)
    proxy_asdz = round((proxy_complexity_ratio - 1.0) * 4.0, 2)
    proxy_elwz = round((0.5 - proxy_pep_score) * 4.0, 2)
    proxy_comb_z = round(float(response_payload.get("regan_z_score") or ((proxy_mmz + proxy_evz + proxy_asdz) / 3.0)), 2)
    proxy_two_sigma = None
    if isinstance(ipr_ci, list) and len(ipr_ci) == 2:
        proxy_two_sigma = abs(float(ipr_ci[1]) - float(ipr_ci[0])) / 2.0

    if ipr_value is not None:
        s_of_ipr = round(0.007 + (0.00015 * ipr_value), 12)
        c_of_ipr = round(0.18 + (0.00012 * ipr_value), 12)
    else:
        s_of_ipr = None
        c_of_ipr = None

    turn_count = int(regan_metrics.get("n_moves") or response_payload.get("analyzed_move_count") or 0)
    t3thr50z = round(t3z + max(0.0, comb_z) * min(1.0, turn_count / 50.0), 2)

    return {
        "Name": _compact_name(target.player_name, target.player_id),
        "Rating": target.official_elo,
        "Rating Used": rating_used,
        "IPR12": ipr12,
        "CombZ": comb_z,
        "PredZ": pred_z,
        "#turns": turn_count,
        "wtfactor": 1,
        "IPR diff": ipr_diff,
        "2sigma": two_sigma,
        "ChallFaced": challenged_faced,
        "s": round(s_value, 6),
        "c": round(c_value, 6),
        "MMZ": mmz,
        "EVZ": evz,
        "ASDZ": asdz,
        "ELWZ": elwz,
        "Engine": Path(settings.stockfish_path).stem.upper() if settings.stockfish_path else "SF",
        "Weights": "UW",
        "T2Z": t2z,
        "T3Z": t3z,
        "T3thr50Z": t3thr50z,
        "sOfIPR": s_of_ipr,
        "cOfIPR": c_of_ipr,
        "CombZ+": max(0.0, comb_z),
        "Pred+": max(0.0, pred_z or 0.0),
        "ProxyIPR12": proxy_ipr,
        "ProxyCombZ": proxy_comb_z,
        "Proxy2sigma": proxy_two_sigma,
        "ProxyS": round(proxy_superhuman_rate, 6),
        "ProxyC": round(proxy_engine_match, 6),
        "ProxyMMZ": proxy_mmz,
        "ProxyEVZ": proxy_evz,
        "ProxyASDZ": proxy_asdz,
        "ProxyELWZ": proxy_elwz,
    }


def regan_rows_to_csv(rows: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=REGAN_CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key) for key in REGAN_CSV_COLUMNS})
    return buf.getvalue()
