from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

from sentinel.config import settings

LOGGER = logging.getLogger(__name__)

# Conservative defaults for scaffold mode.
# Replace with fitted values from your calibration pipeline/dataset.
DEFAULT_CALIBRATION: dict[str, Any] = {
    "bands": [
        {"min_elo": 0, "max_elo": 1399, "expected_acl": 95.0, "std_acl": 24.0},
        {"min_elo": 1400, "max_elo": 1599, "expected_acl": 78.0, "std_acl": 20.0},
        {"min_elo": 1600, "max_elo": 1799, "expected_acl": 63.0, "std_acl": 17.0},
        {"min_elo": 1800, "max_elo": 1999, "expected_acl": 50.0, "std_acl": 14.0},
        {"min_elo": 2000, "max_elo": 2199, "expected_acl": 39.0, "std_acl": 12.0},
        {"min_elo": 2200, "max_elo": 2399, "expected_acl": 31.0, "std_acl": 10.0},
        {"min_elo": 2400, "max_elo": 4000, "expected_acl": 24.0, "std_acl": 8.0},
    ]
}


def _validate_profile(payload: dict[str, Any]) -> bool:
    bands = payload.get("bands")
    if not isinstance(bands, list) or not bands:
        return False

    last_max = None
    for band in bands:
        if not isinstance(band, dict):
            return False
        try:
            min_elo = int(band.get("min_elo"))
            max_elo = int(band.get("max_elo"))
            expected = float(band.get("expected_acl"))
            std = float(band.get("std_acl"))
        except (TypeError, ValueError):
            return False
        if min_elo < 0 or max_elo < min_elo:
            return False
        if expected <= 0 or std <= 0:
            return False
        if last_max is not None and min_elo <= last_max:
            return False
        last_max = max_elo
    return True


def _qa_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"path": str(path), "ok": False, "error": "invalid_json"}
    checks = payload.get("checks") or {}
    ok = True
    failed: list[str] = []
    alert_counts: dict[str, int] = {}
    for name, check in checks.items():
        if not isinstance(check, dict):
            continue
        check_ok = bool(check.get("ok", True))
        if not check_ok:
            ok = False
            failed.append(str(name))
        alerts = check.get("alerts") or check.get("gaps") or []
        alert_counts[str(name)] = len(alerts) if isinstance(alerts, list) else 0
    return {
        "path": str(path),
        "ok": ok,
        "failed_checks": failed,
        "alert_counts": alert_counts,
        "generated_at_utc": payload.get("generated_at_utc"),
        "min_samples_per_band": payload.get("min_samples_per_band"),
    }


@lru_cache(maxsize=1)
def _load_profile_with_meta() -> tuple[dict[str, Any], dict[str, Any]]:
    meta: dict[str, Any] = {
        "source": "default",
        "profile_path": settings.calibration_profile_path,
        "exists": False,
        "valid": False,
    }
    if not settings.calibration_profile_path:
        LOGGER.warning("CALIBRATION_PROFILE_PATH not set; using DEFAULT_CALIBRATION")
        return DEFAULT_CALIBRATION, meta

    p = Path(settings.calibration_profile_path)
    meta["exists"] = p.exists()
    if not p.exists():
        LOGGER.warning("Calibration profile not found at %s; using DEFAULT_CALIBRATION", p)
        return DEFAULT_CALIBRATION, meta
    try:
        payload = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        LOGGER.warning("Calibration profile invalid JSON; using DEFAULT_CALIBRATION")
        return DEFAULT_CALIBRATION, meta
    if not _validate_profile(payload):
        LOGGER.warning("Calibration profile failed validation; using DEFAULT_CALIBRATION")
        return DEFAULT_CALIBRATION, meta

    meta["valid"] = True
    meta["source"] = "file"
    qa_path = p.with_suffix(".qa.json")
    meta["qa"] = _qa_summary(qa_path)
    return payload, meta


@lru_cache(maxsize=1)
def _load_profile() -> dict[str, Any]:
    payload, _ = _load_profile_with_meta()
    return payload


def calibration_status() -> dict[str, Any]:
    payload, meta = _load_profile_with_meta()
    bands = payload.get("bands") or []
    min_elo = None
    max_elo = None
    for band in bands:
        try:
            min_elo = int(band.get("min_elo")) if min_elo is None else min(min_elo, int(band.get("min_elo")))
            max_elo = int(band.get("max_elo")) if max_elo is None else max(max_elo, int(band.get("max_elo")))
        except Exception:
            continue
    return {
        "source": meta.get("source"),
        "profile_path": meta.get("profile_path"),
        "exists": meta.get("exists"),
        "valid": meta.get("valid"),
        "band_count": len(bands),
        "coverage_min_elo": min_elo,
        "coverage_max_elo": max_elo,
        "schema_version": payload.get("schema_version"),
        "profile_version": payload.get("profile_version"),
        "generated_at_utc": payload.get("generated_at_utc"),
        "qa": meta.get("qa"),
    }


def regan_acl_params_for_elo(elo: int) -> tuple[float, float]:
    profile = _load_profile()
    bands = profile.get("bands", [])
    for b in bands:
        if int(b.get("min_elo", 0)) <= elo <= int(b.get("max_elo", 9999)):
            expected = float(b.get("expected_acl", 60.0))
            std = max(1.0, float(b.get("std_acl", 15.0)))
            return expected, std
    return 60.0, 15.0
