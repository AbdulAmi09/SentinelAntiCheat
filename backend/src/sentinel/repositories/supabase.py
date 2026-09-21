from __future__ import annotations

import json
import random
import ssl
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class SupabaseConfig:
    url: str
    service_role_key: str
    schema: str = "public"


class SupabaseRepository:
    def __init__(self, cfg: SupabaseConfig) -> None:
        self.cfg = cfg
        self._ssl_context = ssl.create_default_context()
        self._ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

    def _headers(self, prefer: str | None = None) -> dict[str, str]:
        h = {
            "apikey": self.cfg.service_role_key,
            "Authorization": f"Bearer {self.cfg.service_role_key}",
            "Content-Type": "application/json",
            "Accept-Profile": self.cfg.schema,
            "Content-Profile": self.cfg.schema,
        }
        if prefer:
            h["Prefer"] = prefer
        return h

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, error.HTTPError):
            return int(getattr(exc, "code", 500)) >= 500
        if isinstance(exc, (error.URLError, TimeoutError, ssl.SSLError)):
            text = str(exc).lower()
            markers = (
                "timed out",
                "temporarily unavailable",
                "connection reset",
                "bad record mac",
                "sslv3 alert bad record mac",
                "eof occurred in violation of protocol",
            )
            return any(m in text for m in markers) or True
        return False

    def _post(self, path: str, payload: list[dict], prefer: str | None = None) -> None:
        endpoint = f"{self.cfg.url.rstrip('/')}/rest/v1/{path}"
        body = json.dumps(payload).encode("utf-8")
        max_attempts = 4
        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            req = request.Request(endpoint, data=body, method="POST", headers=self._headers(prefer))
            try:
                with request.urlopen(req, timeout=20, context=self._ssl_context):
                    return
            except Exception as exc:
                last_exc = exc
                if attempt >= max_attempts or not self._is_retryable(exc):
                    raise
                backoff = (0.35 * (2 ** (attempt - 1))) + random.uniform(0.0, 0.15)
                time.sleep(backoff)
        if last_exc is not None:
            raise last_exc

<<<<<<< HEAD
    def _upsert(self, path: str, payload: list[dict], *, on_conflict: str) -> None:
        self._post(
            f"{path}?on_conflict={on_conflict}",
            payload,
            prefer="resolution=merge-duplicates,return=minimal",
        )

=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        cleaned = (value or "").strip()
        return cleaned or None

    @classmethod
    def _resolve_federation_id(cls, event_id: str, federation_id: str | None = None) -> str | None:
        explicit = cls._normalize_text(federation_id)
        if explicit:
            return explicit
        event_value = cls._normalize_text(event_id)
        if event_value and "::" in event_value:
            candidate, _ = event_value.split("::", 1)
            return candidate.strip() or None
        return None

    def persist_analysis(
        self,
        *,
        player_id: str,
        event_id: str,
        federation_id: str | None,
        event_type: str,
        audit_id: str,
        weighted_risk_score: float,
        regan_threshold_used: float,
        natural_occurrence_statement: str,
        natural_occurrence_probability: float | None,
        model_version: str,
        feature_schema_version: str,
        report_schema_version: str,
        legal_disclaimer_text: str,
        human_review_required: bool,
        response_payload: dict,
        request_payload: dict,
    ) -> None:
        resolved_federation_id = self._resolve_federation_id(event_id, federation_id)
<<<<<<< HEAD
        review_status = "under_review" if human_review_required else "pending"
        report_version = int(response_payload.get("report_version") or 1)
        report_locked = bool(response_payload.get("report_locked") or False)
        analysis_row = {
            "player_id": player_id,
            "event_id": event_id,
            "federation_id": resolved_federation_id,
            "external_audit_id": audit_id,
            "risk_tier": response_payload["risk_tier"],
            "confidence": response_payload["confidence"],
            "analyzed_move_count": response_payload["analyzed_move_count"],
            "triggered_signals": response_payload["triggered_signals"],
            "weighted_risk_score": weighted_risk_score,
            "event_type": event_type,
            "regan_threshold_used": regan_threshold_used,
            "natural_occurrence_statement": natural_occurrence_statement,
            "natural_occurrence_probability": natural_occurrence_probability,
            "model_version": model_version,
            "feature_schema_version": feature_schema_version,
            "report_schema_version": report_schema_version,
            "report_version": report_version,
            "report_locked": report_locked,
            "report_locked_at": response_payload.get("report_locked_at"),
            "legal_disclaimer_text": legal_disclaimer_text,
            "human_review_required": human_review_required,
            "review_status": review_status,
            "explainability_method": response_payload.get("explainability_method"),
            "explainability_items": response_payload.get("explainability_items"),
            "ml_fusion_source": response_payload.get("ml_fusion_source"),
            "ml_primary_score": response_payload.get("ml_primary_score"),
            "ml_secondary_score": response_payload.get("ml_secondary_score"),
            "input_hash": audit_id,
            "explanation": response_payload["explanation"],
            "signals": response_payload["signals"],
            "raw_request": request_payload,
            "raw_response": response_payload,
        }
        optional_analysis_fields = (
            "chain_hash",
            "prev_chain_hash",
            "evidence_report",
            "behavioral_metrics",
            "environmental_metrics",
            "identity_confidence",
            "confidence_intervals",
            "report_workflow",
        )
        for field_name in optional_analysis_fields:
            if field_name in response_payload:
                analysis_row[field_name] = response_payload.get(field_name)
        for numeric_field in ("ipr_estimate", "pep_score", "regan_z_score"):
            field_value = response_payload.get(numeric_field)
            if field_value is not None:
                analysis_row[numeric_field] = field_value
        if resolved_federation_id is not None:
            self._upsert(
                "federations",
                [{"id": resolved_federation_id, "name": resolved_federation_id}],
                on_conflict="id",
            )
        self._upsert(
            "players",
            [{"id": player_id}],
            on_conflict="id",
=======
        if resolved_federation_id is not None:
            self._post(
                "federations?on_conflict=id",
                [{"id": resolved_federation_id, "name": resolved_federation_id}],
                prefer="resolution=merge-duplicates,return=minimal",
            )
        self._post(
            "players?on_conflict=id",
            [{"id": player_id}],
            prefer="resolution=merge-duplicates,return=minimal",
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        )
        event_row = {"id": event_id, "event_type": event_type}
        if resolved_federation_id is not None:
            event_row["federation_id"] = resolved_federation_id
<<<<<<< HEAD
        self._upsert(
            "events",
            [event_row],
            on_conflict="id",
        )
        analysis_row["review_status"] = review_status
        analysis_row["federation_id"] = resolved_federation_id
        self._upsert(
            "analyses",
            [analysis_row],
            on_conflict="external_audit_id",
        )
        self._upsert(
            "report_versions",
            [
                {
                    "analysis_external_audit_id": audit_id,
                    "version_no": report_version,
                    "locked": report_locked,
=======
        self._post(
            "events?on_conflict=id",
            [event_row],
            prefer="resolution=merge-duplicates,return=minimal",
        )
        review_status = "under_review" if human_review_required else "pending"
        self._post(
            "analyses",
            [
                {
                    "player_id": player_id,
                    "event_id": event_id,
                    "federation_id": resolved_federation_id,
                    "external_audit_id": audit_id,
                    "risk_tier": response_payload["risk_tier"],
                    "confidence": response_payload["confidence"],
                    "analyzed_move_count": response_payload["analyzed_move_count"],
                    "triggered_signals": response_payload["triggered_signals"],
                    "weighted_risk_score": weighted_risk_score,
                    "event_type": event_type,
                    "regan_threshold_used": regan_threshold_used,
                    "natural_occurrence_statement": natural_occurrence_statement,
                    "natural_occurrence_probability": natural_occurrence_probability,
                    "model_version": model_version,
                    "feature_schema_version": feature_schema_version,
                    "report_schema_version": report_schema_version,
                    "report_version": int(response_payload.get("report_version") or 1),
                    "report_locked": bool(response_payload.get("report_locked") or False),
                    "report_locked_at": response_payload.get("report_locked_at"),
                    "legal_disclaimer_text": legal_disclaimer_text,
                    "human_review_required": human_review_required,
                    "review_status": review_status,
                    "explainability_method": response_payload.get("explainability_method"),
                    "explainability_items": response_payload.get("explainability_items"),
                    "ml_fusion_source": response_payload.get("ml_fusion_source"),
                    "ml_primary_score": response_payload.get("ml_primary_score"),
                    "ml_secondary_score": response_payload.get("ml_secondary_score"),
                    "input_hash": audit_id,
                    "explanation": response_payload["explanation"],
                    "signals": response_payload["signals"],
                    "raw_request": request_payload,
                    "raw_response": response_payload,
                }
            ],
            prefer="return=minimal",
        )
        self._post(
            "report_versions?on_conflict=analysis_external_audit_id,version_no",
            [
                {
                    "analysis_external_audit_id": audit_id,
                    "version_no": int(response_payload.get("report_version") or 1),
                    "locked": bool(response_payload.get("report_locked") or False),
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                    "locked_at": response_payload.get("report_locked_at"),
                    "disclaimer_text": legal_disclaimer_text,
                    "report_body": response_payload,
                }
            ],
<<<<<<< HEAD
            on_conflict="analysis_external_audit_id,version_no",
=======
            prefer="resolution=merge-duplicates,return=minimal",
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        )

    def persist_pgn_details(
        self,
        *,
        event_id: str,
        federation_id: str | None,
        player_id: str,
        opponent_player_id: str,
        player_color: str,
        pgn_text: str,
        parsed_games: list[dict[str, Any]],
    ) -> None:
        resolved_federation_id = self._resolve_federation_id(event_id, federation_id)
        if resolved_federation_id is not None:
<<<<<<< HEAD
            self._upsert(
                "federations",
                [{"id": resolved_federation_id, "name": resolved_federation_id}],
                on_conflict="id",
            )
        # Ensure player/opponent/event identities exist for FK constraints.
        self._upsert(
            "players",
            [{"id": player_id}, {"id": opponent_player_id}],
            on_conflict="id",
=======
            self._post(
                "federations?on_conflict=id",
                [{"id": resolved_federation_id, "name": resolved_federation_id}],
                prefer="resolution=merge-duplicates,return=minimal",
            )
        # Ensure player/opponent/event identities exist for FK constraints.
        self._post(
            "players?on_conflict=id",
            [{"id": player_id}, {"id": opponent_player_id}],
            prefer="resolution=merge-duplicates,return=minimal",
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        )
        event_row = {"id": event_id}
        if resolved_federation_id is not None:
            event_row["federation_id"] = resolved_federation_id
<<<<<<< HEAD
        self._upsert(
            "events",
            [event_row],
            on_conflict="id",
=======
        self._post(
            "events?on_conflict=id",
            [event_row],
            prefer="resolution=merge-duplicates,return=minimal",
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        )

        white_id = player_id if player_color == "white" else opponent_player_id
        black_id = opponent_player_id if player_color == "white" else player_id

        game_rows: list[dict[str, Any]] = []
        move_feature_rows: list[dict[str, Any]] = []
        engine_eval_rows: list[dict[str, Any]] = []

        for g in parsed_games:
            game_id = g["game_id"]
            game_rows.append(
                {
                    "id": game_id,
                    "event_id": event_id,
                    "white_player_id": white_id,
                    "black_player_id": black_id,
                    "pgn": pgn_text,
                }
            )
            for m in g.get("moves", []):
                ply = int(m["ply"])
                move_feature_rows.append(
                    {
                        "game_id": game_id,
                        "ply": ply,
                        "cp_loss": m.get("cp_loss"),
                        "engine_top1_match": bool(m.get("engine_best") and m.get("player_move") == m.get("engine_best")),
                        "engine_top3_match": bool(m.get("top3_match")),
                        "maia_probability": m.get("maia_probability"),
                        "complexity_score": m.get("complexity_score"),
                        "is_opening_book": m.get("is_opening_book", False),
                        "is_tablebase": m.get("is_tablebase", False),
                        "is_forced": m.get("is_forced", False),
                        "time_spent_seconds": m.get("time_spent_seconds"),
                    }
                )
                engine_eval_rows.append(
                    {
                        "game_id": game_id,
                        "move_number": int((ply + 1) // 2),
                        "top1": m.get("engine_best"),
                        "top3": [m.get("engine_best")] if m.get("engine_best") else None,
                        "centipawn_loss": m.get("cp_loss"),
                        "best_eval_cp": 0,
                        "played_eval_cp": -float(m.get("cp_loss") or 0),
                        "think_time": m.get("time_spent_seconds"),
                    }
                )

        if game_rows:
<<<<<<< HEAD
            self._upsert(
                "games",
                game_rows,
                on_conflict="id",
=======
            self._post(
                "games?on_conflict=id",
                game_rows,
                prefer="resolution=merge-duplicates,return=minimal",
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            )
        if move_feature_rows:
            self._post("move_features", move_feature_rows, prefer="return=minimal")
        if engine_eval_rows:
            self._post("engine_evals", engine_eval_rows, prefer="return=minimal")

    def persist_partner_job(
        self,
        *,
        job_id: str,
        api_key_id: str,
<<<<<<< HEAD
        federation_id: str | None,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        game_id: str,
        player_id: str,
        raw_payload: dict[str, Any],
        status: str,
        webhook_url: str | None,
    ) -> None:
<<<<<<< HEAD
        self._upsert(
=======
        self._post(
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            "partner_jobs",
            [
                {
                    "job_id": job_id,
                    "api_key_id": api_key_id,
<<<<<<< HEAD
                    "federation_id": federation_id,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                    "game_id": game_id,
                    "player_id": player_id,
                    "raw_payload": raw_payload,
                    "status": status,
                    "webhook_url": webhook_url,
                }
            ],
<<<<<<< HEAD
            on_conflict="job_id",
        )
        self._upsert(
=======
            prefer="return=minimal",
        )
        self._post(
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            "partner_payloads",
            [
                {
                    "job_id": job_id,
                    "api_key_id": api_key_id,
<<<<<<< HEAD
                    "federation_id": federation_id,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                    "game_id": game_id,
                    "player_id": player_id,
                    "payload": raw_payload,
                }
            ],
<<<<<<< HEAD
            on_conflict="job_id",
=======
            prefer="return=minimal",
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        )

    @staticmethod
    def error_text(exc: Exception) -> str:
        if isinstance(exc, error.HTTPError):
            try:
                return exc.read().decode("utf-8", errors="ignore")
            except Exception:
                return str(exc)
        return str(exc)
