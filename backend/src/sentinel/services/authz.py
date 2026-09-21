from __future__ import annotations

from fastapi import HTTPException

from sentinel.config import settings

RoleName = str

_ROLE_PERMISSIONS: dict[RoleName, set[str]] = {
    "arbiter": {
        "analyze",
        "analyze_pgn",
        "tournament_summary",
        "dashboard_feed",
        "report_get",
        "report_generate",
        "case_create",
        "case_list",
        "case_get",
        "case_update",
        "case_note_add",
        "case_note_list",
        "case_evidence_add",
        "case_evidence_list",
        "case_flag_add",
        "case_flag_list",
<<<<<<< HEAD
        "case_review_add",
        "case_review_list",
        "case_signoff_add",
        "case_signoff_list",
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        "otb_incident_create",
        "otb_incident_list",
        "otb_camera_ingest",
        "otb_board_ingest",
        "otb_camera_list",
        "otb_board_list",
        "visuals",
        "tournament_dashboard",
        "player_profile",
        "live_create",
        "live_get",
        "live_ingest",
        "live_risk",
        "demo_analyze",
    },
    "chief_arbiter": {
        "analyze",
        "analyze_pgn",
        "tournament_summary",
        "dashboard_feed",
        "report_get",
        "report_lock",
        "report_version",
        "system_status",
        "report_generate",
        "case_create",
        "case_list",
        "case_get",
        "case_update",
        "case_note_add",
        "case_note_list",
        "case_evidence_add",
        "case_evidence_list",
        "case_flag_add",
        "case_flag_list",
<<<<<<< HEAD
        "case_review_add",
        "case_review_list",
        "case_signoff_add",
        "case_signoff_list",
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        "otb_incident_create",
        "otb_incident_list",
        "otb_camera_ingest",
        "otb_board_ingest",
        "otb_camera_list",
        "otb_board_list",
        "visuals",
        "tournament_dashboard",
        "player_profile",
        "live_create",
        "live_get",
        "live_ingest",
        "live_risk",
        "demo_analyze",
        "partner_key_list",
        "partner_key_create",
        "partner_key_disable",
        "partner_key_rotate",
<<<<<<< HEAD
        "partner_key_reveal",
        "partner_job_list",
        "partner_session_list",
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    },
    "federation_admin": {
        "analyze",
        "analyze_pgn",
        "tournament_summary",
        "dashboard_feed",
        "report_get",
        "report_lock",
        "report_version",
        "system_status",
        "report_generate",
        "case_create",
        "case_list",
        "case_get",
        "case_update",
        "case_note_add",
        "case_note_list",
        "case_evidence_add",
        "case_evidence_list",
        "case_flag_add",
        "case_flag_list",
<<<<<<< HEAD
        "case_review_add",
        "case_review_list",
        "case_signoff_add",
        "case_signoff_list",
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        "otb_incident_create",
        "otb_incident_list",
        "otb_camera_ingest",
        "otb_board_ingest",
        "otb_camera_list",
        "otb_board_list",
        "visuals",
        "tournament_dashboard",
        "player_profile",
        "live_create",
        "live_get",
        "live_ingest",
        "live_risk",
        "demo_analyze",
        "partner_key_list",
        "partner_key_create",
        "partner_key_disable",
        "partner_key_rotate",
<<<<<<< HEAD
        "partner_key_reveal",
        "partner_job_list",
        "partner_session_list",
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    },
    "system_admin": {"*"},
}


def normalize_role(role: str | None) -> RoleName:
    value = (role or "").strip().lower().replace("-", "_")
    return value or "system_admin"


def authorize_action(role: str | None, action: str) -> RoleName:
    normalized = normalize_role(role)
    if not settings.rbac_enabled:
        return normalized
    allowed = _ROLE_PERMISSIONS.get(normalized)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Unknown role '{normalized}'")
    if "*" in allowed or action in allowed:
        return normalized
    raise HTTPException(status_code=403, detail=f"Role '{normalized}' is not allowed to perform '{action}'")


def _event_federation(event_id: str | None) -> str | None:
    if not event_id:
        return None
    parts = event_id.split("::", 1)
    if len(parts) != 2:
        return None
    return parts[0].strip() or None


def enforce_tenant_scope(role: str, federation_id: str | None, event_id: str | None = None) -> None:
    if not settings.tenant_enforcement_enabled:
        return
    if role == "system_admin":
        return
    if not federation_id:
        raise HTTPException(status_code=403, detail="X-Federation-Id is required for non-system roles")
    event_fed = _event_federation(event_id)
    if event_fed and event_fed != federation_id:
        raise HTTPException(
            status_code=403,
            detail=f"Federation scope mismatch: event '{event_id}' is not in federation '{federation_id}'",
        )
