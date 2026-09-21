from __future__ import annotations

import hmac
import hashlib
import json
import secrets
import threading
import time
from queue import Queue
from typing import Any

import requests

from sentinel.repositories.partner import PartnerRepository
from sentinel.schemas import AnalyzeRequest, AnalyzePgnRequest, HistoricalProfile
from sentinel.services.feature_pipeline import compute_features
from sentinel.services.pgn_engine_pipeline import create_engine_context, game_to_inputs, parse_pgn_games
from sentinel.services.risk_engine import classify_with_meta
from sentinel.services.signal_layers import evaluate_all_layers


class PartnerJobWorker:
    def __init__(self, repo: PartnerRepository) -> None:
        self.repo = repo
        self.queue: Queue[str] = Queue()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def enqueue(self, job_id: str) -> None:
        self.queue.put(job_id)

    def poll_db_once(self) -> int:
        queued = self.repo.list_queued_jobs(limit=100)
        for job_id in queued:
            self.enqueue(job_id)
        return len(queued)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                job_id = self.queue.get(timeout=0.5)
            except Exception:
                self.poll_db_once()
                continue
            try:
                self._process_job(job_id)
            except Exception:
                continue

    def _process_job(self, job_id: str) -> None:
        job = self.repo.get_job(job_id)
        if not job:
            return
        payload = job.get("raw_payload") or {}
        pgn_text = payload.get("pgn") or ""
        player_id = payload.get("player_id") or "unknown"
        player_color = payload.get("player_color") or "white"
        event_id = payload.get("game_id") or job.get("game_id") or "partner-game"
        official_elo = int(payload.get("official_elo") or 1500)

        games = parse_pgn_games(pgn_text)
        if not games:
            result = {"status": "failed", "message": "PGN parse failed"}
            self.repo.update_job_result(job_id, "failed", None, None, result, job.get("webhook_attempts", 0), False)
            return

        try:
            ctx = create_engine_context(official_elo)
        except ValueError as exc:
            result = {"status": "failed", "message": str(exc)}
            self.repo.update_job_result(job_id, "failed", None, None, result, job.get("webhook_attempts", 0), False)
            return
        try:
            parsed_games = [
                game_to_inputs(
                    game=g,
                    game_id=f"{event_id}:{player_id}:partner",
                    player_color=player_color,
                    ctx=ctx,
                )
                for g in games
            ]
        finally:
            ctx.close()

        behavioral = extract_behavioral_metrics(payload)
        device_fp = payload.get("device_fingerprint") or {}
        fp_hash = ""
        if isinstance(device_fp, dict):
            fp_hash = str(device_fp.get("fingerprint_hash") or "")
        if fp_hash:
            stats = self.repo.record_device_fingerprint(fp_hash, player_id, device_fp)
            behavioral["identity_confidence"] = {
                "fingerprint_hash": fp_hash,
                "seen_count": stats.get("seen_count"),
                "distinct_players": stats.get("distinct_players"),
                "distinct_count": stats.get("distinct_count"),
                "shared_device": bool((stats.get("distinct_count") or 0) > 1),
            }
        normalized = AnalyzeRequest(
            player_id=player_id,
            event_id=event_id,
            event_type="online",
            official_elo=official_elo,
            games=parsed_games,
            historical=HistoricalProfile(),
            behavioral=behavioral,
        )
        features = compute_features(normalized)
        layers = evaluate_all_layers(features)
        tier, conf, explanation, weighted_score, fusion_meta = classify_with_meta(features, layers)
        result = {
            "player_id": player_id,
            "game_id": event_id,
            "risk_tier": tier.value,
            "risk_score": float(weighted_score),
            "confidence": float(conf),
            "signals": [
                {"name": l.name, "triggered": l.triggered, "score": float(l.score), "threshold": float(l.threshold)}
                for l in layers
            ],
            "explanation": explanation,
            "ml_fusion_source": fusion_meta.get("source"),
            "behavioral": behavioral,
        }

        webhook_delivered, attempts = deliver_webhook(job, self.repo, result)
        status = "complete" if webhook_delivered else "webhook_failed"
        self.repo.update_job_result(job_id, status, tier.value, float(weighted_score), result, attempts, webhook_delivered)


def generate_keypair() -> tuple[str, str]:
    return secrets.token_urlsafe(24), secrets.token_urlsafe(32)


def deliver_webhook(job: dict, repo: PartnerRepository, result: dict) -> tuple[bool, int]:
    webhook_url = job.get("webhook_url")
    secret = ""
    try:
        key = repo.get_key(job.get("api_key_id"), reveal=True)
        secret = key.get("secret") or ""
    except Exception:
        secret = ""
    if not webhook_url:
        return False, int(job.get("webhook_attempts") or 0)

    behavioral = result.get("behavioral") or {}
    payload = {
        "job_id": job.get("job_id"),
        "game_id": job.get("game_id"),
        "player_id": job.get("player_id"),
        "status": "complete",
        "risk_level": result.get("risk_tier"),
        "risk_score": result.get("risk_score"),
        "summary": "Statistical analysis complete. Human review recommended for elevated findings.",
        "signals": result.get("signals", []),
        "behavioral": behavioral,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    attempts = int(job.get("webhook_attempts") or 0)
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = (
        hmac.new(str(secret or "").encode("utf-8"), body, hashlib.sha256).hexdigest() if secret else ""
    )
    headers = {"Content-Type": "application/json", "X-Sentinel-Job-Id": str(job.get("job_id") or "")}
    if signature:
        headers["X-Sentinel-Signature"] = signature

    for delay in (0, 30, 300, 1800):
        if delay:
            time.sleep(delay)
        attempts += 1
        try:
            resp = requests.post(webhook_url, data=body, headers=headers, timeout=10)
            if resp.status_code == 200:
                return True, attempts
        except Exception:
            continue
    return False, attempts


def extract_behavioral_metrics(payload: dict) -> dict:
    per_move = payload.get("per_move_summary") or []
    window_events = payload.get("window_events") or []
    page_events = payload.get("page_events") or []
    mouse_events = payload.get("mouse_events") or []
    environment = payload.get("environment") or {}
    camera_events = payload.get("camera_events") or []
    camera_summary = payload.get("camera_summary")

    def _count(events, etype):
        return len([e for e in events if (e.get("type") or e.get("event")) == etype])

    copy_paste = _count(page_events, "copy") + _count(page_events, "paste") + _count(page_events, "cut")
    focus_loss = _count(window_events, "blur")
    tab_switch = focus_loss

    path_vals = [m.get("path_straightness") for m in per_move if m.get("path_straightness") is not None]
    straightness = sum(path_vals) / len(path_vals) if path_vals else None

    timing_vals = [m.get("time_spent_seconds") for m in per_move if m.get("time_spent_seconds") is not None]
    avg_time = sum(timing_vals) / len(timing_vals) if timing_vals else None

    drag_vals = [m.get("drag_duration_ms") for m in per_move if m.get("drag_duration_ms") is not None]
    avg_drag = sum(drag_vals) / len(drag_vals) if drag_vals else None

    dwell_vals = [m.get("hover_dwell_on_played_square_ms") for m in per_move if m.get("hover_dwell_on_played_square_ms") is not None]
    avg_dwell = sum(dwell_vals) / len(dwell_vals) if dwell_vals else None

    squares_vals = [m.get("squares_visited_count") for m in per_move if m.get("squares_visited_count") is not None]
    avg_squares = sum(squares_vals) / len(squares_vals) if squares_vals else None

    reaction_vals = [m.get("reaction_time_ms") for m in per_move if m.get("reaction_time_ms") is not None]
    avg_reaction = sum(reaction_vals) / len(reaction_vals) if reaction_vals else None

    return {
        "copy_paste_events": copy_paste,
        "focus_loss_count": focus_loss,
        "tab_switch_count": tab_switch,
        "avg_mouse_path_straightness": straightness,
        "avg_move_time_seconds": avg_time,
        "mouse_event_count": len(mouse_events),
        "avg_drag_duration_ms": avg_drag,
        "avg_hover_dwell_played_square_ms": avg_dwell,
        "avg_squares_visited": avg_squares,
        "avg_reaction_time_ms": avg_reaction,
        "environment": environment,
        "camera_summary": camera_summary if isinstance(camera_summary, dict) else summarize_camera_events(camera_events),
    }


def summarize_camera_events(events: list[dict]) -> dict:
    summary: dict[str, int | float] = {
        "event_count": 0,
        "face_missing_count": 0,
        "multiple_faces_count": 0,
        "gaze_away_count": 0,
        "low_light_count": 0,
        "microphone_active_count": 0,
        "motion_detected_count": 0,
        "recording_started_count": 0,
        "recording_stopped_count": 0,
        "snapshot_taken_count": 0,
    }
    if not isinstance(events, list):
        return summary
    summary["event_count"] = len(events)
    for evt in events:
        etype = str(evt.get("type") or evt.get("event") or evt.get("eventType") or evt.get("event_type") or "").lower()
        if etype in {"face_missing", "no_face"}:
            summary["face_missing_count"] += 1
        elif etype in {"multiple_faces", "multi_face"}:
            summary["multiple_faces_count"] += 1
        elif etype in {"gaze_away", "look_away"}:
            summary["gaze_away_count"] += 1
        elif etype in {"low_light"}:
            summary["low_light_count"] += 1
        elif etype in {"mic_active", "microphone_active"}:
            summary["microphone_active_count"] += 1
        elif etype == "motion_detected":
            summary["motion_detected_count"] += 1
        elif etype == "recording_started":
            summary["recording_started_count"] += 1
        elif etype == "recording_stopped":
            summary["recording_stopped_count"] += 1
        elif etype == "snapshot_taken":
            summary["snapshot_taken_count"] += 1
    return summary
