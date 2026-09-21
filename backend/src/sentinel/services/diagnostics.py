from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sentinel.config import settings
from sentinel.services.calibration import calibration_status
from sentinel.services.maia import maia_status
from sentinel.services.ml_fusion import ml_fusion_status

LOGGER = logging.getLogger(__name__)


def _path_status(path: str | None) -> dict[str, Any]:
    if not path:
        return {"path": None, "exists": False}
    return {"path": path, "exists": Path(path).exists()}


def system_status() -> dict[str, Any]:
    calibration = calibration_status()
    ml_fusion = ml_fusion_status()
    maia = maia_status()
    engine = _path_status(settings.stockfish_path)
    opening_book = _path_status(settings.polyglot_book_path)
    tablebase = _path_status(settings.syzygy_path)

    lc0_path = maia.get("lc0_path")
    lc0_ready = bool(lc0_path and Path(str(lc0_path)).exists())
    maia_models_detected = bool(maia.get("available_count"))
    ml_models_loaded = bool(ml_fusion.get("models_loaded"))
    # ML fusion is an optional scoring layer; the analysis pipeline still functions
    # in heuristic mode when those artifacts are missing or corrupted.
    analysis_pipeline_operational = bool(engine.get("exists") and lc0_ready and maia_models_detected)

    warnings: list[str] = []
    if calibration.get("source") != "file":
        warnings.append("Calibration profile not loaded from file; using defaults")
    qa = calibration.get("qa") or {}
    if qa and qa.get("ok") is False:
        warnings.append("Calibration QA report has failures")
    if settings.ml_fusion_enabled and not ml_fusion.get("models_present"):
        warnings.append("ML fusion enabled but no model artifacts are available")
    if settings.ml_fusion_enabled and ml_fusion.get("models_present") and not ml_fusion.get("models_loaded"):
        warnings.append("ML model artifacts found but failed to load")
    if not settings.encryption_key:
        warnings.append("Encryption key not configured; partner secrets stored in plaintext in non-prod environments")
    if maia.get("models_dir"):
        if maia.get("lc0_path") and not Path(str(maia.get("lc0_path"))).exists():
            warnings.append("Maia lc0 binary missing; Maia probabilities disabled")
        if not maia.get("available_count"):
            warnings.append("Maia weights not found; Maia probabilities disabled")
    if not engine.get("exists"):
        warnings.append("Stockfish path missing; PGN analysis will fail")

    return {
        "generated_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "app_env": settings.app_env,
        "model_version": settings.model_version,
        "feature_schema_version": settings.feature_schema_version,
        "report_schema_version": settings.report_schema_version,
        "calibration": calibration,
        "ml_fusion": ml_fusion,
        "maia": maia,
        "engine": engine,
        "opening_book": opening_book,
        "tablebase": tablebase,
        "supabase_configured": bool(settings.supabase_url and settings.supabase_service_role_key),
        "rbac_enabled": settings.rbac_enabled,
        "tenant_enforcement_enabled": settings.tenant_enforcement_enabled,
        "lc0_ready": lc0_ready,
        "maia_models_detected": maia_models_detected,
        "ml_models_loaded": ml_models_loaded,
        "analysis_pipeline_operational": analysis_pipeline_operational,
        "warnings": warnings,
    }


def startup_checks() -> dict[str, Any]:
    status = system_status()
    for warning in status.get("warnings", []):
        LOGGER.warning("Startup check: %s", warning)
    return status
