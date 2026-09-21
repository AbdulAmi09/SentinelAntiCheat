from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import chess.pgn

CSV_COLUMNS = [
    "source",
    "source_game_id",
    "event_id",
    "event_type",
    "game_date",
    "time_control",
    "rated",
    "player_id",
    "opponent_id",
    "player_color",
    "official_elo",
    "opponent_elo",
    "result",
    "avg_acl",
    "account_status",
    "is_banned",
    "label",
    "ingested_at_utc",
]

CHESSCOM_BASE = "https://api.chess.com/pub"


@dataclass
class StatusMeta:
    account_status: str = "unknown"
    is_banned: bool = False
    label: str = "clean"


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _str_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"1", "true", "yes", "y"}
    return bool(v)


def _as_int(v: Any) -> int | None:
    try:
        if v is None or v == "":
            return None
        return int(float(v))
    except (TypeError, ValueError):
        return None


def _as_float(v: Any) -> float | None:
    try:
        if v is None or v == "":
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _open_text_auto(path: Path):
    suffix = path.suffix.lower()
    if suffix == ".gz":
        return gzip.open(path, mode="rt", encoding="utf-8", newline="")
    if suffix == ".zst":
        try:
            import zstandard as zstd  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Reading .zst requires 'zstandard'. Install with: pip install zstandard") from exc

        fh = path.open("rb")
        stream = zstd.ZstdDecompressor().stream_reader(fh)
        return io.TextIOWrapper(stream, encoding="utf-8")
    return path.open("r", encoding="utf-8", newline="")


def _read_status_map(path: Path | None) -> dict[str, StatusMeta]:
    if path is None:
        return {}
    out: dict[str, StatusMeta] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            username = (row.get("username") or row.get("player_id") or "").strip().lower()
            if not username:
                continue
            banned_raw = row.get("is_banned")
            status = (row.get("account_status") or row.get("status") or "unknown").strip()
            label = (row.get("label") or "").strip().lower() or ("banned" if _str_bool(banned_raw) else "clean")
            out[username] = StatusMeta(
                account_status=status or "unknown",
                is_banned=_str_bool(banned_raw),
                label=label,
            )
    return out


def _write_rows(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _winner_result(winner: str | None, color: str) -> str:
    if winner is None:
        return "draw"
    return "win" if winner == color else "loss"


def etl_lichess(args: argparse.Namespace) -> None:
    status_map = _read_status_map(Path(args.status_map)) if args.status_map else {}
    ingested_at = _iso_now()
    out_rows: list[dict[str, Any]] = []

    in_path = Path(args.input)
    with _open_text_auto(in_path) as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                game = json.loads(line)
            except json.JSONDecodeError:
                continue

            players = game.get("players") or {}
            winner = game.get("winner")
            game_id = str(game.get("id") or f"lichess-{idx}")
            time_control = str(game.get("speed") or "")
            rated = bool(game.get("rated", False))
            ts_ms = game.get("createdAt")
            game_date = ""
            if isinstance(ts_ms, (int, float)):
                game_date = datetime.fromtimestamp(float(ts_ms) / 1000.0, tz=UTC).date().isoformat()

            for color in ("white", "black"):
                side = players.get(color) or {}
                opp = players.get("black" if color == "white" else "white") or {}
                user_obj = side.get("user") or {}
                opp_user = opp.get("user") or {}
                username = str(user_obj.get("name") or "unknown").strip()
                opponent = str(opp_user.get("name") or "unknown").strip()
                if username.lower() == "unknown":
                    continue

                meta = status_map.get(username.lower(), StatusMeta(label=args.label_default))
                analysis = side.get("analysis") or {}
                acl = _as_float(analysis.get("acpl"))

                out_rows.append(
                    {
                        "source": "lichess",
                        "source_game_id": game_id,
                        "event_id": str(game.get("tournament") or game.get("event") or "lichess-event"),
                        "event_type": "online",
                        "game_date": game_date,
                        "time_control": time_control,
                        "rated": str(rated).lower(),
                        "player_id": username,
                        "opponent_id": opponent,
                        "player_color": color,
                        "official_elo": _as_int(side.get("rating")) or "",
                        "opponent_elo": _as_int(opp.get("rating")) or "",
                        "result": _winner_result(winner, color),
                        "avg_acl": "" if acl is None else round(acl, 4),
                        "account_status": meta.account_status,
                        "is_banned": str(meta.is_banned).lower(),
                        "label": meta.label,
                        "ingested_at_utc": ingested_at,
                    }
                )

    _write_rows(out_rows, Path(args.output))
    print(f"Lichess rows written: {len(out_rows)} -> {args.output}")


def _fetch_json(url: str, user_agent: str, timeout: int = 30) -> Any:
    req = Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)


def _chesscom_status(username: str, user_agent: str) -> StatusMeta:
    url = f"{CHESSCOM_BASE}/player/{quote(username)}"
    try:
        payload = _fetch_json(url, user_agent)
    except (HTTPError, URLError, TimeoutError):
        return StatusMeta(account_status="unknown", is_banned=False, label="clean")

    status = str(payload.get("status") or "").lower()
    is_banned = "fair_play" in status or "closed" in status
    label = "banned" if is_banned else "clean"
    return StatusMeta(account_status=status or "unknown", is_banned=is_banned, label=label)


def etl_chesscom(args: argparse.Namespace) -> None:
    usernames_path = Path(args.usernames_file)
    usernames = [x.strip() for x in usernames_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not usernames:
        raise RuntimeError("No usernames found in usernames file")

    ingested_at = _iso_now()
    out_rows: list[dict[str, Any]] = []

    for username in usernames:
        status = _chesscom_status(username, args.user_agent)
        archives_url = f"{CHESSCOM_BASE}/player/{quote(username)}/games/archives"
        try:
            archives_payload = _fetch_json(archives_url, args.user_agent)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"WARN: skipping {username} archives fetch: {exc}", file=sys.stderr)
            continue

        archives = list(archives_payload.get("archives") or [])
        if args.max_archives_per_user > 0:
            archives = archives[-args.max_archives_per_user :]

        for archive_url in archives:
            try:
                monthly = _fetch_json(str(archive_url), args.user_agent)
            except (HTTPError, URLError, TimeoutError) as exc:
                print(f"WARN: archive fetch failed {archive_url}: {exc}", file=sys.stderr)
                continue
            for game in monthly.get("games") or []:
                white = game.get("white") or {}
                black = game.get("black") or {}
                white_user = str(white.get("username") or "").strip()
                black_user = str(black.get("username") or "").strip()

                if white_user.lower() == username.lower():
                    color = "white"
                    side = white
                    opp = black
                    opponent = black_user
                elif black_user.lower() == username.lower():
                    color = "black"
                    side = black
                    opp = white
                    opponent = white_user
                else:
                    continue

                accuracies = game.get("accuracies") or {}
                side_accuracy = _as_float(accuracies.get(color))
                avg_acl = None if side_accuracy is None else max(0.0, 100.0 - side_accuracy)

                out_rows.append(
                    {
                        "source": "chesscom",
                        "source_game_id": str(game.get("uuid") or game.get("url") or ""),
                        "event_id": str(game.get("tournament") or game.get("url") or "chesscom-event"),
                        "event_type": "online",
                        "game_date": str(game.get("end_time") or ""),
                        "time_control": str(game.get("time_class") or game.get("time_control") or ""),
                        "rated": "true",
                        "player_id": username,
                        "opponent_id": opponent,
                        "player_color": color,
                        "official_elo": _as_int(side.get("rating")) or "",
                        "opponent_elo": _as_int(opp.get("rating")) or "",
                        "result": str(side.get("result") or "unknown"),
                        "avg_acl": "" if avg_acl is None else round(avg_acl, 4),
                        "account_status": status.account_status,
                        "is_banned": str(status.is_banned).lower(),
                        "label": status.label,
                        "ingested_at_utc": ingested_at,
                    }
                )

    _write_rows(out_rows, Path(args.output))
    print(f"Chess.com rows written: {len(out_rows)} -> {args.output}")


def _safe_header_int(game: chess.pgn.Game, key: str) -> int | None:
    return _as_int(game.headers.get(key, ""))


def etl_twic(args: argparse.Namespace) -> None:
    in_path = Path(args.input)
    out_rows: list[dict[str, Any]] = []
    ingested_at = _iso_now()

    with in_path.open("r", encoding="utf-8", errors="replace") as f:
        game_index = 0
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            game_index += 1

            white = str(game.headers.get("White") or "unknown")
            black = str(game.headers.get("Black") or "unknown")
            event = str(game.headers.get("Event") or "twic")
            date = str(game.headers.get("Date") or "")
            result = str(game.headers.get("Result") or "*")
            game_id = str(game.headers.get("Site") or f"twic-{game_index}")

            for color in ("white", "black"):
                if color == "white":
                    player = white
                    opponent = black
                    player_elo = _safe_header_int(game, "WhiteElo")
                    opp_elo = _safe_header_int(game, "BlackElo")
                    side_result = "win" if result == "1-0" else ("draw" if result == "1/2-1/2" else "loss")
                else:
                    player = black
                    opponent = white
                    player_elo = _safe_header_int(game, "BlackElo")
                    opp_elo = _safe_header_int(game, "WhiteElo")
                    side_result = "win" if result == "0-1" else ("draw" if result == "1/2-1/2" else "loss")

                out_rows.append(
                    {
                        "source": "twic",
                        "source_game_id": game_id,
                        "event_id": event,
                        "event_type": "otb",
                        "game_date": date,
                        "time_control": str(game.headers.get("TimeControl") or ""),
                        "rated": "true",
                        "player_id": player,
                        "opponent_id": opponent,
                        "player_color": color,
                        "official_elo": player_elo or "",
                        "opponent_elo": opp_elo or "",
                        "result": side_result,
                        "avg_acl": "",
                        "account_status": "otb_baseline",
                        "is_banned": "false",
                        "label": args.label_default,
                        "ingested_at_utc": ingested_at,
                    }
                )

    _write_rows(out_rows, Path(args.output))
    print(f"TWIC rows written: {len(out_rows)} -> {args.output}")


def merge_sources(args: argparse.Namespace) -> None:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()

    for input_path in args.inputs:
        path = Path(input_path)
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (
                    row.get("source", ""),
                    row.get("source_game_id", ""),
                    row.get("player_id", ""),
                    row.get("player_color", ""),
                )
                if key in seen:
                    continue
                seen.add(key)
                normalized = {k: row.get(k, "") for k in CSV_COLUMNS}
                merged.append(normalized)

    _write_rows(merged, Path(args.output))
    print(f"Merged rows written: {len(merged)} -> {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ETL pipeline for Sentinel calibration datasets")
    sub = parser.add_subparsers(dest="command", required=True)

    p_lichess = sub.add_parser("lichess", help="Transform Lichess NDJSON export into normalized calibration CSV")
    p_lichess.add_argument("--input", required=True, help="Path to Lichess NDJSON/JSONL (.gz/.zst supported)")
    p_lichess.add_argument("--output", required=True, help="Output CSV path")
    p_lichess.add_argument("--status-map", default="", help="Optional CSV of username/account_status/is_banned/label")
    p_lichess.add_argument("--label-default", default="clean", help="Default label if status map does not include player")
    p_lichess.set_defaults(func=etl_lichess)

    p_chesscom = sub.add_parser("chesscom", help="Fetch Chess.com public archives and normalize game rows")
    p_chesscom.add_argument("--usernames-file", required=True, help="Text file with one username per line")
    p_chesscom.add_argument("--output", required=True, help="Output CSV path")
    p_chesscom.add_argument("--max-archives-per-user", type=int, default=12)
    p_chesscom.add_argument("--user-agent", default="SentinelCalibrationETL/1.0")
    p_chesscom.set_defaults(func=etl_chesscom)

    p_twic = sub.add_parser("twic", help="Transform TWIC PGN into normalized OTB baseline rows")
    p_twic.add_argument("--input", required=True, help="TWIC PGN file path")
    p_twic.add_argument("--output", required=True, help="Output CSV path")
    p_twic.add_argument("--label-default", default="clean")
    p_twic.set_defaults(func=etl_twic)

    p_merge = sub.add_parser("merge", help="Merge normalized source CSVs into one deduplicated dataset")
    p_merge.add_argument("--inputs", nargs="+", required=True, help="Input normalized CSV files")
    p_merge.add_argument("--output", required=True, help="Merged output CSV path")
    p_merge.set_defaults(func=merge_sources)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
