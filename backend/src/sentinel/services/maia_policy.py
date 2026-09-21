from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chess
import chess.engine

from sentinel.config import settings

LOGGER = logging.getLogger(__name__)

MAIA_BUCKETS = [1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
MOVE_RE = re.compile(r"\b([a-h][1-8][a-h][1-8][qrbn]?)\b")
P_RE = re.compile(r"P:\s*([0-9]+(?:\.[0-9]+)?)%?", re.IGNORECASE)


def _normalize_path(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    return cleaned or None


def _select_bucket(elo: int, available: list[int] | None = None) -> int:
    buckets = available or MAIA_BUCKETS
    if not buckets:
        return MAIA_BUCKETS[0]
    if elo <= buckets[0]:
        return buckets[0]
    if elo >= buckets[-1]:
        return buckets[-1]
    return min(buckets, key=lambda b: abs(b - elo))


def _bucket_weight_path(base_dir: Path, bucket: int) -> str | None:
    bucket_dir = base_dir / f"maia-{bucket}"
    if bucket_dir.exists():
        preferred = bucket_dir / "model.pb"
        if preferred.exists():
            return str(preferred)
        preferred_gz = bucket_dir / "model.pb.gz"
        if preferred_gz.exists():
            return str(preferred_gz)
        fallback = next(bucket_dir.glob("*.pb"), None) or next(bucket_dir.glob("*.pb.gz"), None)
        if fallback is not None:
            return str(fallback)
    flat = base_dir / f"maia-{bucket}.pb"
    if flat.exists():
        return str(flat)
    flat_gz = base_dir / f"maia-{bucket}.pb.gz"
    if flat_gz.exists():
        return str(flat_gz)
    return None


def _weights_path_for_bucket(bucket: int) -> str | None:
    override = _normalize_path(settings.maia_model_path)
    if override:
        return override if Path(override).exists() else None
    base_dir = _normalize_path(settings.maia_models_dir)
    if not base_dir:
        return None
    return _bucket_weight_path(Path(base_dir), bucket)


def _parse_policy(strings: list[str]) -> dict[str, float]:
    entries: list[tuple[str, float]] = []
    for line in strings:
        move_match = MOVE_RE.search(line)
        prob_match = P_RE.search(line)
        if not move_match or not prob_match:
            continue
        uci = move_match.group(1)
        try:
            prob = float(prob_match.group(1))
        except ValueError:
            continue
        entries.append((uci, prob))

    if not entries:
        return {}
    max_p = max(p for _, p in entries)
    if max_p > 1.0:
        entries = [(uci, p / 100.0) for uci, p in entries]
    total = sum(p for _, p in entries)
    if total > 0:
        entries = [(uci, p / total) for uci, p in entries]
    return {uci: p for uci, p in entries}


def _maia_limit() -> chess.engine.Limit:
    kwargs: dict[str, float | int] = {}
    if settings.maia_nodes > 0:
        kwargs["nodes"] = settings.maia_nodes
    if settings.maia_time_seconds > 0:
        kwargs["time"] = settings.maia_time_seconds
    return chess.engine.Limit(**kwargs)


@dataclass
class MaiaPolicyContext:
    engine: chess.engine.SimpleEngine
    weights_path: str
    bucket: int

    def close(self) -> None:
        try:
            self.engine.quit()
        except Exception:
            pass

    def move_probability(self, board: chess.Board, move: chess.Move) -> float | None:
        try:
            info = self.engine.analyse(
                board,
                _maia_limit(),
                info=chess.engine.INFO_ALL,
            )
        except Exception as exc:
            LOGGER.warning("Maia policy analyse failed: %s", exc)
            return None

        if isinstance(info, list):
            info = info[0] if info else {}
        strings = info.get("string") or []
        if isinstance(strings, str):
            strings = [strings]
        policy = _parse_policy(list(strings))
        if not policy:
            return None
        return policy.get(move.uci())


def create_maia_context(official_elo: int | None) -> MaiaPolicyContext | None:
    lc0_path = _normalize_path(settings.maia_lc0_path)
    if not lc0_path:
        return None
    if not Path(lc0_path).exists():
        LOGGER.warning("MAIA_LC0_PATH not found at %s", lc0_path)
        return None

    elo = int(official_elo or 1500)
    available = maia_models_available().get("buckets") or []
    bucket = _select_bucket(elo, available)
    weights_path = _weights_path_for_bucket(bucket)
    if not weights_path:
        LOGGER.warning("No Maia weights found for bucket %s", bucket)
        return None

    args = [
        lc0_path,
        f"--weights={weights_path}",
        f"--threads={settings.maia_threads}",
        f"--backend={settings.maia_backend}",
        "--verbose-move-stats",
    ]
    if settings.maia_backend_opts:
        args.append(f"--backend-opts={settings.maia_backend_opts}")
    if settings.maia_temperature is not None:
        args.append(f"--temperature={settings.maia_temperature}")
    if settings.maia_temp_decay_moves:
        args.append(f"--tempdecay-moves={settings.maia_temp_decay_moves}")

    try:
        engine = chess.engine.SimpleEngine.popen_uci(args)
    except Exception as exc:
        LOGGER.warning("Failed to start Maia lc0 engine: %s", exc)
        return None

    return MaiaPolicyContext(engine=engine, weights_path=weights_path, bucket=bucket)


def maia_models_available() -> dict[str, Any]:
    base_dir = _normalize_path(settings.maia_models_dir)
    if not base_dir:
        return {"models_dir": None, "buckets": [], "count": 0}
    base_path = Path(base_dir)
    if not base_path.exists():
        return {"models_dir": base_dir, "buckets": [], "count": 0}
    found: list[int] = []
    for bucket in MAIA_BUCKETS:
        if _bucket_weight_path(base_path, bucket):
            found.append(bucket)
    return {"models_dir": base_dir, "buckets": found, "count": len(found)}
