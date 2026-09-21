from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Iterable, Iterator

import joblib
import numpy as np
import requests
import xgboost as xgb
import zstandard as zstd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split

import chess.pgn
import chess.engine
import chess.polyglot
import chess.syzygy

import sentinel.config as config_module
from sentinel.config import settings
from sentinel.schemas import AnalyzeRequest, GameInput, HistoricalProfile, MoveInput
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.ml_fusion import _feature_vector
from sentinel.services.pgn_engine_pipeline import EngineContext, game_to_inputs
from sentinel.services.signal_layers import evaluate_all_layers
from sentinel.services.maia_policy import maia_models_available


FEATURE_NAMES = [
    "regan_z_score",
    "regan_threshold",
    "engine_match_pct",
    "top3_match_pct",
    "avg_centipawn_loss",
    "accuracy_in_complex_positions",
    "complexity_accuracy_ratio",
    "superhuman_move_rate",
    "rating_adjusted_move_probability",
    "move_quality_uniformity_score",
    "round_anomaly_clustering_score",
    "maia_humanness_score",
    "engine_maia_disagreement",
    "avg_engine_gap_cp",
    "avg_position_complexity",
    "avg_engine_rank",
    "hard_best_move_rate",
    "rating_band_index",
    "style_deviation_score",
    "timing_confidence_score",
    "layer1_ipr_movequality",
    "layer2_complexity_adjusted",
    "layer3_time_complexity",
    "layer4_historical_baseline",
    "layer5_behavioral_consistency",
    "historical_volatility_score",
    "multi_tournament_anomaly_score",
    "career_growth_curve_score",
]

RATING_BANDS = [
    (800, 1200),
    (1200, 1800),
    (1800, 2400),
    (2400, 10000),
]

DEFAULT_BAND_TARGETS = [250, 250, 250, 250]


@dataclass
class TrainingSample:
    vector: np.ndarray
    engine_match_percentage: float
    maia_agreement_percentage: float


def _log(msg: str) -> None:
    print(msg, flush=True)


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _rating_band_index(elo: int) -> int:
    for idx, (low, high) in enumerate(RATING_BANDS):
        if elo < high:
            return idx
    return len(RATING_BANDS) - 1


def _scaled_band_targets(max_games: int) -> list[int]:
    if max_games <= 0:
        return [0, 0, 0, 0]
    scale = max_games / float(sum(DEFAULT_BAND_TARGETS))
    scaled = [int(round(t * scale)) for t in DEFAULT_BAND_TARGETS]
    diff = max_games - sum(scaled)
    idx = 0
    while diff != 0:
        step = 1 if diff > 0 else -1
        scaled[idx % len(scaled)] = max(0, scaled[idx % len(scaled)] + step)
        diff -= step
        idx += 1
    return scaled


def _require_engine_assets() -> None:
    if not config_module.settings.stockfish_path:
        raise SystemExit("STOCKFISH_PATH is required for PGN-based feature extraction.")
    if not config_module.settings.maia_lc0_path:
        raise SystemExit("MAIA_LC0_PATH is required for Maia-based feature extraction.")
    available = maia_models_available()
    if not available.get("count"):
        raise SystemExit("No Maia model weights found in MAIA_MODELS_DIR.")


def _request_with_retry(
    url: str,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
) -> requests.Response | None:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=30, stream=False)
            if resp.status_code == 429:
                wait = 1.5 * (attempt + 1)
                _log(f"Lichess rate limit hit; retrying in {wait:.1f}s...")
                import time
                time.sleep(wait)
                continue
            return resp
        except Exception as exc:
            last_exc = exc
            wait = 1.5 * (attempt + 1)
            _log(f"Lichess request failed; retrying in {wait:.1f}s...")
            import time
            time.sleep(wait)
    if last_exc:
        _log(f"Lichess request failed after retries: {last_exc}")
    return None


def _fetch_leaderboard(perf: str, token: str | None) -> list[str]:
    url = f"https://lichess.org/api/player/top/200/{perf}"
    headers = {"Accept": "application/vnd.lichess.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = _request_with_retry(url, headers)
    if resp is None:
        return []
    if resp.status_code != 200:
        return []
    payload = resp.json()
    return [u.get("username") for u in payload.get("users", []) if u.get("username")]


def _fetch_user_rating(username: str, token: str | None) -> int | None:
    url = f"https://lichess.org/api/user/{username}"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = _request_with_retry(url, headers)
    if resp is None or resp.status_code != 200:
        return None
    payload = resp.json()
    perfs = payload.get("perfs") or {}
    ratings: list[int] = []
    for perf in ("blitz", "rapid", "classical"):
        rating = (perfs.get(perf) or {}).get("rating")
        if isinstance(rating, int):
            ratings.append(rating)
        elif isinstance(rating, float):
            ratings.append(int(rating))
    return max(ratings) if ratings else None


def _lichess_list(base_url: str) -> list[str]:
    list_url = f"{base_url.rstrip('/')}/list.txt"
    resp = requests.get(list_url, timeout=30)
    resp.raise_for_status()
    return [line.strip() for line in resp.text.splitlines() if line.strip()]


def _latest_lichess_month(base_url: str) -> str:
    pattern = re.compile(r"lichess_db_standard_rated_(\d{4}-\d{2})\.pgn\.zst")
    months: list[str] = []
    for name in _lichess_list(base_url):
        match = pattern.search(name)
        if match:
            months.append(match.group(1))
    if not months:
        raise SystemExit("Unable to determine latest Lichess PGN month from list.txt.")
    return sorted(months)[-1]


def _lichess_url(month: str) -> str:
    return f"https://database.lichess.org/standard/lichess_db_standard_rated_{month}.pgn.zst"


def _stream_lichess_games_user(username: str, token: str | None, max_games: int) -> Iterator[chess.pgn.Game]:
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": 100,
        "rated": "true",
        "perfType": "blitz,rapid,classical",
        "moves": "true",
        "tags": "true",
        "clocks": "true",
        "evals": "false",
        "opening": "true",
        "pgnInJson": "false",
    }
    headers = {"Accept": "application/x-chess-pgn"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, headers=headers, stream=True, timeout=30)
            resp.raise_for_status()
            text = io.TextIOWrapper(resp.raw, encoding="utf-8", errors="ignore")
            while True:
                try:
                    game = chess.pgn.read_game(text)
                except Exception:
                    break
                if game is None:
                    break
                yield game
            return
        except Exception as exc:
            wait = 1.5 * (attempt + 1)
            _log(f"Warning: failed to stream games for {username} (attempt {attempt + 1}/3): {exc}")
            import time
            time.sleep(wait)
    return


def _collect_lichess_api_dataset(
    output_path: Path,
    max_games: int,
    token: str | None,
    users: list[str],
    per_user_max: int,
) -> Path:
    if per_user_max > 10:
        _log(f"Per-user max capped at 10 (requested {per_user_max}).")
        per_user_max = 10
    targets = _scaled_band_targets(max_games)
    counts = [0, 0, 0, 0]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)

    seed_users = set(users)

    queue = list(seed_users)
    known_players = set(seed_users)
    rating_cache: dict[str, int] = {}
    games_per_player: dict[str, int] = {}
    seen_games: set[str] = set()

    _log(f"Collecting rated games via Lichess API (target {max_games} games).")
    _log(f"Band targets: 800-1200={targets[0]}, 1200-1800={targets[1]}, 1800-2400={targets[2]}, 2400+={targets[3]}")
    _log(f"Seed players: {len(seed_users)}")

    with output_path.open("w", encoding="utf-8") as out:
        while queue and sum(counts) < max_games:
            user = queue.pop(0)
            if games_per_player.get(user, 0) >= per_user_max:
                continue
            if user not in rating_cache:
                rating = _fetch_user_rating(user, token)
                if rating is None:
                    continue
                rating_cache[user] = rating
            rating = rating_cache[user]
            band = _rating_band_index(rating)

            fetched = 0
            for game in _stream_lichess_games_user(user, token, max_games=per_user_max):
                fetched += 1
                site = (game.headers.get("Site") or "").strip()
                game_id = site.rsplit("/", 1)[-1] if site else f"{game.headers.get('Event','')}-{fetched}"
                if game_id in seen_games:
                    continue
                seen_games.add(game_id)

                white = (game.headers.get("White") or "").strip()
                black = (game.headers.get("Black") or "").strip()
                for opp in (white, black):
                    if opp and opp not in known_players:
                        known_players.add(opp)
                        queue.append(opp)

                if counts[band] >= targets[band]:
                    continue
                if games_per_player.get(user, 0) >= per_user_max:
                    break
                out.write(game.accept(exporter))
                out.write("\n\n")
                counts[band] += 1
                games_per_player[user] = games_per_player.get(user, 0) + 1
                if sum(counts) >= max_games:
                    break

            _log(f"User {user}: scanned {fetched} games, dataset counts {counts}")

    _log(f"Saved training dataset to {output_path}")
    if sum(counts) < max_games:
        _log("Warning: Unable to fill all rating-band targets. Provide more seed players or rerun.")
    return output_path


def _collect_lichess_games_by_id(
    output_path: Path,
    max_games: int,
    token: str | None,
    ids: list[str],
) -> Path:
    targets = _scaled_band_targets(max_games)
    counts = [0, 0, 0, 0]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
    headers = {"Accept": "application/x-chess-pgn"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    _log(f"Collecting rated games by ID via Lichess API (target {max_games} games).")
    with output_path.open("w", encoding="utf-8") as out:
        for gid in ids:
            if sum(counts) >= max_games:
                break
            url = f"https://lichess.org/api/game/export/{gid}"
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                continue
            text = io.StringIO(resp.text)
            game = chess.pgn.read_game(text)
            if game is None:
                continue
            white_elo = _int_tag(game, "WhiteElo", default=0)
            black_elo = _int_tag(game, "BlackElo", default=0)
            if white_elo <= 0 or black_elo <= 0:
                continue
            avg_elo = int((white_elo + black_elo) / 2)
            band = _rating_band_index(avg_elo)
            if counts[band] >= targets[band]:
                continue
            out.write(game.accept(exporter))
            out.write("\n\n")
            counts[band] += 1

    _log(f"Saved training dataset to {output_path}")
    if sum(counts) < max_games:
        _log("Warning: Unable to fill all rating-band targets using provided game IDs.")
    return output_path


def _open_pgn_stream(path: Path) -> Iterator[chess.pgn.Game]:
    if path.suffix.lower() == ".pgn":
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            while True:
                game = chess.pgn.read_game(handle)
                if game is None:
                    break
                yield game
        return
    if path.suffix.lower().endswith(".zst") or path.name.endswith(".pgn.zst"):
        with path.open("rb") as raw:
            dctx = zstd.ZstdDecompressor()
            with dctx.stream_reader(raw) as reader:
                text = io.TextIOWrapper(reader, encoding="utf-8", errors="ignore")
                while True:
                    game = chess.pgn.read_game(text)
                    if game is None:
                        break
                    yield game
        return
    raise SystemExit(f"Unsupported PGN format: {path}")


def _open_pgn_stream_from_url(url: str) -> Iterator[chess.pgn.Game]:
    _log(f"Streaming PGN from {url}")
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()
    dctx = zstd.ZstdDecompressor()
    with dctx.stream_reader(resp.raw) as reader:
        text = io.TextIOWrapper(reader, encoding="utf-8", errors="ignore")
        while True:
            game = chess.pgn.read_game(text)
            if game is None:
                break
            yield game


def _int_tag(game: chess.pgn.Game, key: str, default: int = 1500) -> int:
    try:
        return int(game.headers.get(key, "") or default)
    except ValueError:
        return default


def _game_id(game: chess.pgn.Game, idx: int) -> str:
    site = game.headers.get("Site")
    if site:
        return site.strip()
    return f"lichess-game-{idx}"


def _build_move_inputs(
    game: chess.pgn.Game,
    game_id: str,
    player_color: str,
    engine: chess.engine.SimpleEngine,
    book: chess.polyglot.MemoryMappedReader | None,
    tablebase: chess.syzygy.Tablebase | None,
    maia_ctx: object | None,
) -> GameInput:
    ctx = EngineContext(engine=engine, book=book, tablebase=tablebase, maia=maia_ctx)  # type: ignore[arg-type]
    return game_to_inputs(game=game, game_id=game_id, player_color=player_color, ctx=ctx)


def _sample_from_game_input(
    game_input: GameInput,
    player_id: str,
    elo: int,
    history: list[GameInput],
) -> TrainingSample | None:
    if not game_input.moves:
        return None

    req = AnalyzeRequest(
        player_id=player_id,
        event_id="ml-training",
        event_type="online",
        official_elo=elo,
        games=[*history, game_input],
        historical=HistoricalProfile(),
    )
    features = compute_features(req)
    layers = evaluate_all_layers(features)
    vector = _feature_vector(features, layers).reshape(-1)
    if len(vector) != len(FEATURE_NAMES):
        raise SystemExit("Feature vector length mismatch. Update FEATURE_NAMES to match ml_fusion feature vector.")

    maia_probs = [m.maia_probability for m in game_input.moves if m.maia_probability is not None]
    if not maia_probs:
        return None
    maia_agreement = float(mean(maia_probs))
    return TrainingSample(
        vector=vector,
        engine_match_percentage=float(features.engine_match_pct),
        maia_agreement_percentage=maia_agreement,
    )


def _nearest_bucket(elo: int, available: list[int]) -> int:
    buckets = sorted(available) if available else [1500]
    if elo <= buckets[0]:
        return buckets[0]
    if elo >= buckets[-1]:
        return buckets[-1]
    return min(buckets, key=lambda b: abs(b - elo))


def _create_maia_ctx(elo: int):
    import sentinel.services.maia_policy as _maia_pol
    _maia_pol.settings = config_module.settings
    return _maia_pol.create_maia_context(elo)


def _iter_move_feature_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def _coerce_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value) if value not in (None, "") else default
    except ValueError:
        return default


def _coerce_int(value: str | None, default: int = 0) -> int:
    try:
        return int(float(value)) if value not in (None, "") else default
    except ValueError:
        return default


def _moves_from_feature_rows(rows: list[dict[str, str]]) -> list[MoveInput]:
    moves: list[MoveInput] = []
    for row in rows:
        cp_loss = _coerce_float(row.get("cp_loss"))
        engine_best = row.get("engine_best") or "e2e4"
        player_move = row.get("player_move") or ("e2e4" if row.get("engine_top1_match") == "true" else "d2d4")
        top3 = row.get("engine_top3_match")
        top3_match = (top3 or "").lower() in {"true", "1", "yes"} if top3 is not None else False
        if not top3_match and row.get("engine_top1_match"):
            top3_match = (row.get("engine_top1_match") or "").lower() in {"true", "1", "yes"}
        maia_raw = row.get("maia_probability")
        maia_prob = _coerce_float(maia_raw, default=-1.0) if maia_raw not in (None, "") else None
        if maia_prob is not None and maia_prob < 0:
            maia_prob = None
        time_raw = row.get("time_spent_seconds")
        time_val = _coerce_float(time_raw, default=-1.0) if time_raw not in (None, "") else None
        if time_val is not None and time_val < 0:
            time_val = None
        moves.append(
            MoveInput(
                ply=_coerce_int(row.get("ply"), default=len(moves) + 1),
                engine_best=engine_best,
                player_move=player_move,
                cp_loss=cp_loss,
                top3_match=top3_match,
                maia_probability=maia_prob,
                complexity_score=_coerce_int(row.get("complexity_score"), default=1),
                candidate_moves_within_50cp=_coerce_int(row.get("candidate_moves_within_50cp"), default=1),
                best_second_gap_cp=_coerce_float(row.get("best_second_gap_cp")),
                eval_swing_cp=_coerce_float(row.get("eval_swing_cp")),
                best_eval_cp=_coerce_float(row.get("best_eval_cp")),
                played_eval_cp=_coerce_float(row.get("played_eval_cp")),
                is_opening_book=(row.get("is_opening_book") or "").lower() in {"true", "1", "yes"},
                is_tablebase=(row.get("is_tablebase") or "").lower() in {"true", "1", "yes"},
                is_forced=(row.get("is_forced") or "").lower() in {"true", "1", "yes"},
                time_spent_seconds=time_val,
            )
        )
    return moves


def _load_user_list(explicit: str | None, file_path: str | None) -> list[str]:
    users: list[str] = []
    if explicit:
        users.extend([u.strip() for u in explicit.split(",") if u.strip()])
    if file_path:
        p = Path(file_path)
        if p.exists():
            users.extend([line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()])
    return list(dict.fromkeys(users))


def _build_samples_from_features_csv(path: Path, max_games: int) -> list[TrainingSample]:
    _log(f"Loading move features from {path}")
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in _iter_move_feature_rows(path):
        game_id = row.get("game_id") or row.get("game") or "game-unknown"
        key = f"{game_id}:{row.get('player_id') or row.get('player_color') or 'player'}"
        grouped.setdefault(key, []).append(row)
        if len(grouped) >= max_games:
            break

    samples: list[TrainingSample] = []
    for key, rows in grouped.items():
        moves = _moves_from_feature_rows(rows)
        if not moves:
            continue
        game_input = GameInput(game_id=key, moves=moves)
        req = AnalyzeRequest(
            player_id=key,
            event_id="ml-training",
            event_type="online",
            official_elo=_coerce_int(rows[0].get("official_elo"), default=1500),
            games=[game_input],
            historical=HistoricalProfile(),
        )
        features = compute_features(req)
        layers = evaluate_all_layers(features)
        vector = _feature_vector(features, layers).reshape(-1)
        if len(vector) != len(FEATURE_NAMES):
            raise SystemExit("Feature vector length mismatch. Update FEATURE_NAMES to match ml_fusion feature vector.")
        maia_probs = [m.maia_probability for m in moves if m.maia_probability is not None]
        if not maia_probs:
            continue
        samples.append(
            TrainingSample(
                vector=vector,
                engine_match_percentage=float(features.engine_match_pct),
                maia_agreement_percentage=float(mean(maia_probs)),
            )
        )
    _log(f"Prepared {len(samples)} samples from move features.")
    return samples


def _build_samples_from_pgn(
    games: Iterable[chess.pgn.Game],
    max_games: int,
    max_moves: int,
) -> list[TrainingSample]:
    _require_engine_assets()
    _log("Starting PGN feature extraction using Stockfish + Maia...")

    # Use config_module.settings directly so we always have the refreshed settings
    engine = chess.engine.SimpleEngine.popen_uci(config_module.settings.stockfish_path)
    book = chess.polyglot.open_reader(config_module.settings.polyglot_book_path) if config_module.settings.polyglot_book_path else None
    tablebase = chess.syzygy.open_tablebase(config_module.settings.syzygy_path) if config_module.settings.syzygy_path else None

    # Ensure maia_policy has refreshed settings before discovering buckets
    import sentinel.services.maia_policy as _maia_pol
    _maia_pol.settings = config_module.settings

    available = _maia_pol.maia_models_available().get("buckets") or []
    _log(f"Maia buckets available: {available}")

    maia_cache: dict[int, object | None] = {}
    samples: list[TrainingSample] = []
    history_map: dict[str, list[GameInput]] = {}

    try:
        for idx, game in enumerate(games, start=1):
            if idx > max_games:
                break
            game_id = _game_id(game, idx)

            white_elo = _int_tag(game, "WhiteElo", default=1500)
            black_elo = _int_tag(game, "BlackElo", default=1500)

            for color, elo in (("white", white_elo), ("black", black_elo)):
                bucket = _nearest_bucket(elo, available)
                if bucket not in maia_cache:
                    maia_cache[bucket] = _create_maia_ctx(elo)
                maia_ctx = maia_cache[bucket]

                game_input = _build_move_inputs(game, game_id, color, engine, book, tablebase, maia_ctx)
                if not game_input.moves:
                    _log(f"  Game {idx} ({color}): 0 moves returned — skipping")
                    continue
                if max_moves and len(game_input.moves) > max_moves:
                    game_input = GameInput(game_id=game_input.game_id, moves=game_input.moves[:max_moves])

                player_tag = game.headers.get("White") if color == "white" else game.headers.get("Black")
                player_id = (player_tag or f"{game_id}:{color}").strip()
                history = history_map.get(player_id, [])
                sample = _sample_from_game_input(
                    game_input=game_input,
                    player_id=player_id,
                    elo=elo,
                    history=history[-50:],
                )
                if sample is not None:
                    samples.append(sample)
                else:
                    _log(f"  Game {idx} ({color}): sample dropped — no maia probabilities")
                history.append(game_input)
                history_map[player_id] = history

            if idx % 10 == 0:
                _log(f"Processed {idx} games; samples collected: {len(samples)}")

    finally:
        try:
            engine.quit()
        except Exception:
            pass
        if book is not None:
            book.close()
        if tablebase is not None:
            tablebase.close()
        for ctx in maia_cache.values():
            if ctx is not None:
                try:
                    ctx.close()
                except Exception:
                    pass

    _log(f"Collected {len(samples)} training samples.")
    return samples


def _train_isolation_forest(x: np.ndarray, contamination: float, seed: int) -> IsolationForest:
    model = IsolationForest(
        n_estimators=300,
        contamination=contamination,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(x)
    return model


def _pseudo_labels(scores: np.ndarray, contamination: float) -> np.ndarray:
    threshold = np.quantile(scores, 1.0 - contamination)
    return (scores >= threshold).astype(int)


def _report_anomaly_distribution(scores: np.ndarray) -> None:
    percentiles = [1, 5, 25, 50, 75, 95, 99]
    stats = {p: float(np.percentile(scores, p)) for p in percentiles}
    _log("Anomaly score distribution (higher = more anomalous):")
    _log(json.dumps(stats, indent=2))


def _train_xgboost(
    x: np.ndarray,
    y: np.ndarray,
    seed: int,
) -> xgb.XGBClassifier:
    model = xgb.XGBClassifier(
        max_depth=5,
        n_estimators=300,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=seed,
        n_jobs=max(1, os.cpu_count() or 1),
    )
    model.fit(x, y)
    return model


def _evaluate_xgboost(model: xgb.XGBClassifier, x_val: np.ndarray, y_val: np.ndarray) -> None:
    preds = model.predict(x_val)
    acc = accuracy_score(y_val, preds)
    precision, recall, f1, _ = precision_recall_fscore_support(y_val, preds, average="binary", zero_division=0)
    _log(f"XGBoost accuracy: {acc:.4f}")
    _log(f"XGBoost precision: {precision:.4f}, recall: {recall:.4f}, f1: {f1:.4f}")
    if len(np.unique(y_val)) > 1:
        proba = model.predict_proba(x_val)[:, 1]
        auc = roc_auc_score(y_val, proba)
        _log(f"XGBoost ROC AUC: {auc:.4f}")


def _feature_importance(model: xgb.XGBClassifier) -> dict[str, float]:
    booster = model.get_booster()
    raw = booster.get_score(importance_type="gain")
    importance: dict[str, float] = {}
    for key, score in raw.items():
        if key.startswith("f"):
            idx = int(key[1:])
            name = FEATURE_NAMES[idx] if idx < len(FEATURE_NAMES) else key
        else:
            name = key
        importance[name] = float(score)
    return dict(sorted(importance.items(), key=lambda x: -x[1]))


def _save_models(
    xgb_model: xgb.XGBClassifier,
    iso_model: IsolationForest,
    out_dir: Path,
) -> None:
    xgb_dir = out_dir / "xgboost" / "v1.0"
    iso_dir = out_dir / "isolation_forest" / "v1.0"
    xgb_dir.mkdir(parents=True, exist_ok=True)
    iso_dir.mkdir(parents=True, exist_ok=True)

    xgb_path = xgb_dir / "xgboost_model.json"
    iso_path = iso_dir / "isolation_forest.pkl"

    xgb_model.save_model(str(xgb_path))
    joblib.dump(iso_model, iso_path)

    manifest = {
        "feature_names": FEATURE_NAMES,
        "xgboost_model": str(xgb_path),
        "isolation_forest_model": str(iso_path),
    }
    with (xgb_dir / "feature_manifest.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    _log(f"Saved XGBoost model to {xgb_path}")
    _log(f"Saved IsolationForest model to {iso_path}")


def _verify_system_status(url: str) -> None:
    _log(f"Verifying Sentinel system status at {url}")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        _log(f"Warning: unable to reach /v1/system-status ({exc}). Start the API and re-run this step.")
        return
    checks = {
        "ml_models_loaded": payload.get("ml_models_loaded"),
        "analysis_pipeline_operational": payload.get("analysis_pipeline_operational"),
    }
    _log(json.dumps(checks, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train Sentinel ML fusion models.")
    parser.add_argument("--features-csv", type=str, help="Move-feature CSV input (preferred when available).")
    parser.add_argument("--pgn-path", type=str, help="Local PGN or PGN.zst file path.")
    parser.add_argument("--lichess-month", type=str, help="Fetch Lichess PGN month, format YYYY-MM.")
    parser.add_argument("--lichess-token", type=str, default=os.getenv("LICHESS_API_TOKEN"), help="Lichess API token.")
    parser.add_argument("--lichess-users-file", type=str, help="File with Lichess usernames (one per line).")
    parser.add_argument("--lichess-users", type=str, help="Comma-separated Lichess usernames.")
    parser.add_argument("--lichess-game-ids", type=str, help="File with Lichess game IDs to export.")
    parser.add_argument("--per-user-max", type=int, default=10, help="Max games to fetch per user.")
    parser.add_argument("--dataset-output", type=str, default="backend/data/raw/training_games.pgn")
    parser.add_argument("--max-games", type=int, default=1000, help="Maximum number of games to process.")
    parser.add_argument("--max-moves", type=int, default=80, help="Max moves per player to analyze.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--status-url", type=str, default="http://localhost:8000/v1/system-status")
    return parser.parse_args()


def main() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    _load_env_file(env_path)
    # Reload settings after .env is loaded
    config_module.settings = config_module.Settings()
    globals()["settings"] = config_module.settings

    # Propagate refreshed settings into all service modules
    import sentinel.services.feature_pipeline as feature_pipeline
    import sentinel.services.maia as maia_service
    import sentinel.services.maia_policy as maia_policy
    import sentinel.services.ml_fusion as ml_fusion
    import sentinel.services.pgn_engine_pipeline as pgn_engine_pipeline

    for mod in (feature_pipeline, maia_service, maia_policy, ml_fusion, pgn_engine_pipeline):
        if hasattr(mod, "settings"):
            mod.settings = config_module.settings

    args = parse_args()
    if args.lichess_month:
        _log("Note: Monthly Lichess dumps are disabled in this pipeline. Using Lichess API streaming instead.")

    if args.features_csv:
        samples = _build_samples_from_features_csv(Path(args.features_csv), max_games=args.max_games)
    else:
        if args.pgn_path:
            games = _open_pgn_stream(Path(args.pgn_path))
            samples = _build_samples_from_pgn(games, max_games=args.max_games, max_moves=args.max_moves)
        else:
            default_users_file = Path(__file__).resolve().parents[1] / "data" / "raw" / "lichess_users_bootstrap.txt"
            output_path = Path(args.dataset_output)
            if args.lichess_game_ids:
                ids = [
                    line.strip()
                    for line in Path(args.lichess_game_ids).read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
                if not ids:
                    raise SystemExit("No Lichess game IDs provided.")
                dataset_path = _collect_lichess_games_by_id(
                    output_path=output_path,
                    max_games=args.max_games,
                    token=args.lichess_token,
                    ids=ids,
                )
            else:
                users = _load_user_list(args.lichess_users, args.lichess_users_file or str(default_users_file))
                dataset_path = _collect_lichess_api_dataset(
                    output_path=output_path,
                    max_games=args.max_games,
                    token=args.lichess_token,
                    users=users,
                    per_user_max=args.per_user_max,
                )
            games = _open_pgn_stream(dataset_path)
            samples = _build_samples_from_pgn(games, max_games=args.max_games, max_moves=args.max_moves)

    if not samples:
        raise SystemExit("No training samples collected. Provide PGNs or move-feature CSVs.")

    x = np.vstack([s.vector for s in samples]).astype(float)

    iso_model = _train_isolation_forest(x, contamination=0.05, seed=args.seed)
    scores = -iso_model.score_samples(x)
    _report_anomaly_distribution(scores)
    labels = _pseudo_labels(scores, contamination=0.05)

    x_train, x_val, y_train, y_val = train_test_split(
        x,
        labels,
        test_size=0.2,
        random_state=args.seed,
        stratify=labels if len(np.unique(labels)) > 1 else None,
    )

    xgb_model = _train_xgboost(x_train, y_train, seed=args.seed)
    if len(np.unique(y_val)) > 1:
        _evaluate_xgboost(xgb_model, x_val, y_val)
    else:
        _log("XGBoost evaluation skipped (single class in validation split).")

    importance = _feature_importance(xgb_model)
    _log("Top feature importance (gain):")
    for name, score in list(importance.items())[:20]:
        _log(f"- {name}: {score:.6f}")

    out_dir = Path(__file__).resolve().parents[1] / "models"
    _save_models(xgb_model, iso_model, out_dir)
    _verify_system_status(args.status_url)


if __name__ == "__main__":
    main()