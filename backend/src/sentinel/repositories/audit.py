from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class AuditRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure()

    def _ensure(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_log (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  model_version TEXT NOT NULL,
                  input_hash TEXT NOT NULL,
                  chain_hash TEXT NOT NULL,
                  prev_chain_hash TEXT,
                  payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS report_workflow (
                  audit_id TEXT PRIMARY KEY,
                  report_version INTEGER NOT NULL DEFAULT 1,
                  report_locked INTEGER NOT NULL DEFAULT 0,
                  report_locked_at TEXT,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS batch_runs (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  event_id TEXT,
                  source_name TEXT,
                  status TEXT NOT NULL,
                  request_json TEXT NOT NULL,
                  response_json TEXT,
                  progress_json TEXT,
                  log_json TEXT,
                  csv_text TEXT,
                  error_text TEXT
                )
                """
            )
            for stmt in (
                "ALTER TABLE audit_log ADD COLUMN chain_hash TEXT",
                "ALTER TABLE audit_log ADD COLUMN prev_chain_hash TEXT",
                "ALTER TABLE batch_runs ADD COLUMN progress_json TEXT",
                "ALTER TABLE batch_runs ADD COLUMN log_json TEXT",
            ):
                try:
                    conn.execute(stmt)
                except sqlite3.OperationalError:
                    pass
            conn.commit()

    def write(self, payload: dict, model_version: str = "v0.1") -> str:
        packed = json.dumps(payload, sort_keys=True)
        input_hash = hashlib.sha256(packed.encode("utf-8")).hexdigest()
        row_id = str(uuid4())
        with sqlite3.connect(self.db_path) as conn:
            prev_chain_hash_row = conn.execute(
                "SELECT chain_hash FROM audit_log ORDER BY created_at DESC LIMIT 1"
            ).fetchone()
            prev_chain_hash = str(prev_chain_hash_row[0]) if prev_chain_hash_row and prev_chain_hash_row[0] else None
            chain_seed = f"{input_hash}:{prev_chain_hash or ''}"
            chain_hash = hashlib.sha256(chain_seed.encode("utf-8")).hexdigest()
            conn.execute(
                (
                    "INSERT INTO audit_log (id, created_at, model_version, input_hash, chain_hash, prev_chain_hash, payload_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (row_id, datetime.now(UTC).isoformat(), model_version, input_hash, chain_hash, prev_chain_hash, packed),
            )
            self._ensure_report_workflow_conn(conn, row_id)
            conn.commit()
        return row_id

    def _ensure_report_workflow_conn(self, conn: sqlite3.Connection, audit_id: str) -> None:
        now = datetime.now(UTC).isoformat()
        conn.execute(
            (
                "INSERT INTO report_workflow (audit_id, report_version, report_locked, report_locked_at, updated_at) "
                "VALUES (?, 1, 0, NULL, ?) "
                "ON CONFLICT(audit_id) DO NOTHING"
            ),
            (audit_id, now),
        )

    def ensure_report_workflow(self, audit_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_report_workflow_conn(conn, audit_id)
            conn.commit()

    def get_report_workflow(self, audit_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_report_workflow_conn(conn, audit_id)
            row = conn.execute(
                (
                    "SELECT report_version, report_locked, report_locked_at "
                    "FROM report_workflow WHERE audit_id = ?"
                ),
                (audit_id,),
            ).fetchone()
            conn.commit()
        if row is None:
            return {"audit_id": audit_id, "report_version": 1, "report_locked": False, "report_locked_at": None}
        return {
            "audit_id": audit_id,
            "report_version": int(row[0]),
            "report_locked": bool(row[1]),
            "report_locked_at": row[2],
        }

    def lock_report(self, audit_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_report_workflow_conn(conn, audit_id)
            now = datetime.now(UTC).isoformat()
            conn.execute(
                (
                    "UPDATE report_workflow "
                    "SET report_locked = 1, report_locked_at = COALESCE(report_locked_at, ?), updated_at = ? "
                    "WHERE audit_id = ?"
                ),
                (now, now, audit_id),
            )
            conn.commit()
        return self.get_report_workflow(audit_id)

    def bump_report_version(self, audit_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            self._ensure_report_workflow_conn(conn, audit_id)
            row = conn.execute(
                "SELECT report_locked FROM report_workflow WHERE audit_id = ?",
                (audit_id,),
            ).fetchone()
            if row is not None and bool(row[0]):
                raise ValueError("Report is locked and cannot be version-bumped")
            now = datetime.now(UTC).isoformat()
            conn.execute(
                (
                    "UPDATE report_workflow "
                    "SET report_version = report_version + 1, updated_at = ? "
                    "WHERE audit_id = ?"
                ),
                (now, audit_id),
            )
            conn.commit()
        return self.get_report_workflow(audit_id)

    def recent(self, *, limit: int = 100, event_id: str | None = None) -> list[dict]:
        q = (
            "SELECT id, created_at, model_version, chain_hash, prev_chain_hash, payload_json "
            "FROM audit_log ORDER BY created_at DESC LIMIT ?"
        )
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(q, (max(1, min(limit, 500)),)).fetchall()

        out: list[dict] = []
        for row_id, created_at, model_version, chain_hash, prev_chain_hash, payload_json in rows:
            try:
                payload = json.loads(payload_json)
            except Exception:
                continue
            req = payload.get("request", {})
            resp = payload.get("response", {})
            if event_id and req.get("event_id") != event_id:
                continue
            out.append(
                {
                    "id": row_id,
                    "created_at": created_at,
                    "model_version": model_version,
                    "chain_hash": chain_hash,
                    "prev_chain_hash": prev_chain_hash,
                    "request": req,
                    "response": resp,
                }
            )
        return out

    def get(self, audit_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, created_at, model_version, chain_hash, prev_chain_hash, payload_json "
                    "FROM audit_log WHERE id = ?"
                ),
                (audit_id,),
            ).fetchone()
        if row is None:
            return None
        row_id, created_at, model_version, chain_hash, prev_chain_hash, payload_json = row
        try:
            payload = json.loads(payload_json)
        except Exception:
            payload = {}
        return {
            "id": row_id,
            "created_at": created_at,
            "model_version": model_version,
            "chain_hash": chain_hash,
            "prev_chain_hash": prev_chain_hash,
            "request": payload.get("request", {}),
            "response": payload.get("response", {}),
        }

    def create_batch_run(self, *, event_id: str | None, source_name: str | None, request_payload: dict) -> dict:
        run_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO batch_runs (id, created_at, updated_at, event_id, source_name, status, request_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (run_id, now, now, event_id, source_name, "queued", json.dumps(request_payload)),
            )
            conn.commit()
        return self.get_batch_run(run_id) or {}

    def complete_batch_run(
        self,
        run_id: str,
        *,
        response_payload: dict | None = None,
        csv_text: str | None = None,
        error_text: str | None = None,
        status: str = "completed",
    ) -> dict:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "UPDATE batch_runs "
                    "SET updated_at = ?, status = ?, response_json = ?, csv_text = ?, error_text = ? "
                    "WHERE id = ?"
                ),
                (
                    now,
                    status,
                    json.dumps(response_payload) if response_payload is not None else None,
                    csv_text,
                    error_text,
                    run_id,
                ),
            )
            conn.commit()
        return self.get_batch_run(run_id) or {}

    def update_batch_run_status(self, run_id: str, status: str) -> dict:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE batch_runs SET updated_at = ?, status = ? WHERE id = ?",
                (now, status, run_id),
            )
            conn.commit()
        return self.get_batch_run(run_id) or {}

    def update_batch_run_progress(
        self,
        run_id: str,
        *,
        status: str | None = None,
        progress: dict | None = None,
        log_message: str | None = None,
    ) -> dict:
        existing = self.get_batch_run(run_id) or {}
        logs = list(existing.get("logs") or [])
        if log_message:
            logs.append({"timestamp": datetime.now(UTC).isoformat(), "message": log_message})
            logs = logs[-200:]
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "UPDATE batch_runs "
                    "SET updated_at = ?, status = COALESCE(?, status), progress_json = ?, log_json = ? "
                    "WHERE id = ?"
                ),
                (
                    now,
                    status,
                    json.dumps(progress) if progress is not None else json.dumps(existing.get("progress")),
                    json.dumps(logs),
                    run_id,
                ),
            )
            conn.commit()
        return self.get_batch_run(run_id) or {}

    def list_batch_runs(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, updated_at, event_id, source_name, status, request_json, response_json, progress_json, log_json, csv_text, error_text "
                    "FROM batch_runs ORDER BY created_at DESC LIMIT ?"
                ),
                (max(1, min(limit, 200)),),
            ).fetchall()
        return [self._row_to_batch_run(row) for row in rows]

    def list_batch_runs_by_status(self, status: str, limit: int = 200) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, updated_at, event_id, source_name, status, request_json, response_json, progress_json, log_json, csv_text, error_text "
                    "FROM batch_runs WHERE status = ? ORDER BY created_at DESC LIMIT ?"
                ),
                (status, max(1, min(limit, 500))),
            ).fetchall()
        return [self._row_to_batch_run(row) for row in rows]

    def get_batch_run(self, run_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, created_at, updated_at, event_id, source_name, status, request_json, response_json, progress_json, log_json, csv_text, error_text "
                    "FROM batch_runs WHERE id = ?"
                ),
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_batch_run(row)

    @staticmethod
    def _row_to_batch_run(row: tuple) -> dict:
        (
            run_id,
            created_at,
            updated_at,
            event_id,
            source_name,
            status,
            request_json,
            response_json,
            progress_json,
            log_json,
            csv_text,
            error_text,
        ) = row
        return {
            "id": run_id,
            "created_at": created_at,
            "updated_at": updated_at,
            "event_id": event_id,
            "source_name": source_name,
            "status": status,
            "request": json.loads(request_json or "{}"),
            "response": json.loads(response_json or "{}") if response_json else None,
            "progress": json.loads(progress_json or "{}") if progress_json else None,
            "logs": json.loads(log_json or "[]") if log_json else [],
            "csv_text": csv_text,
            "error_text": error_text,
        }
