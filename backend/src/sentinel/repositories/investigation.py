from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class InvestigationRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure()

    def _ensure(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cases (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  status TEXT NOT NULL,
                  title TEXT NOT NULL,
                  event_id TEXT,
                  players_json TEXT NOT NULL,
                  summary TEXT,
                  tags_json TEXT NOT NULL,
                  priority TEXT,
                  assigned_to TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_notes (
                  id TEXT PRIMARY KEY,
                  case_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  author TEXT,
                  note_type TEXT,
                  structured_json TEXT NOT NULL,
                  text TEXT,
                  FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_evidence (
                  id TEXT PRIMARY KEY,
                  case_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  evidence_type TEXT NOT NULL,
                  label TEXT,
                  path TEXT,
                  metadata_json TEXT NOT NULL,
                  FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_flags (
                  id TEXT PRIMARY KEY,
                  case_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  flag_type TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  message TEXT NOT NULL,
                  metadata_json TEXT NOT NULL,
                  FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_reports (
                  id TEXT PRIMARY KEY,
                  case_id TEXT,
                  audit_id TEXT,
                  created_at TEXT NOT NULL,
                  report_type TEXT NOT NULL,
                  mode TEXT NOT NULL,
                  format TEXT NOT NULL,
                  content_json TEXT NOT NULL,
                  content_text TEXT,
                  FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_reviews (
                  id TEXT PRIMARY KEY,
                  case_id TEXT NOT NULL,
                  reviewer_user_id TEXT,
                  action TEXT NOT NULL,
                  rationale TEXT,
                  payload_json TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS case_signoffs (
                  id TEXT PRIMARY KEY,
                  case_id TEXT NOT NULL,
                  signer_user_id TEXT,
                  signer_role TEXT NOT NULL,
                  decision TEXT NOT NULL,
                  note TEXT,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(case_id) REFERENCES cases(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS otb_incidents (
                  id TEXT PRIMARY KEY,
                  case_id TEXT,
                  event_id TEXT,
                  player_id TEXT,
                  incident_type TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  description TEXT,
                  occurred_at TEXT,
                  metadata_json TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS otb_camera_events (
                  id TEXT PRIMARY KEY,
                  event_id TEXT,
                  case_id TEXT,
                  player_id TEXT,
                  session_id TEXT,
                  camera_id TEXT,
                  storage_mode TEXT NOT NULL,
                  consent_json TEXT,
                  events_json TEXT NOT NULL,
                  summary_json TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dgt_board_events (
                  id TEXT PRIMARY KEY,
                  event_id TEXT,
                  session_id TEXT,
                  board_serial TEXT,
                  move_uci TEXT,
                  ply INTEGER,
                  fen TEXT,
                  clock_ms INTEGER,
                  raw_json TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS live_sessions (
                  id TEXT PRIMARY KEY,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  event_id TEXT,
                  players_json TEXT NOT NULL,
                  status TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS live_moves (
                  id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  ply INTEGER NOT NULL,
                  move_uci TEXT NOT NULL,
                  time_spent REAL,
                  clock_remaining REAL,
                  complexity REAL,
                  engine_match REAL,
                  maia_prob REAL,
                  tags_json TEXT NOT NULL,
                  FOREIGN KEY(session_id) REFERENCES live_sessions(id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS player_profiles (
                  player_id TEXT PRIMARY KEY,
                  updated_at TEXT NOT NULL,
                  profile_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS player_history (
                  id TEXT PRIMARY KEY,
                  player_id TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  event_id TEXT,
                  snapshot_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def create_case(
        self,
        title: str,
        status: str,
        players: list[str],
        event_id: str | None,
        summary: str | None,
        tags: list[str],
        priority: str | None,
        assigned_to: str | None,
    ) -> dict:
        case_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO cases (id, created_at, updated_at, status, title, event_id, players_json, summary, tags_json, priority, assigned_to) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    case_id,
                    now,
                    now,
                    status,
                    title,
                    event_id,
                    json.dumps(players),
                    summary,
                    json.dumps(tags),
                    priority,
                    assigned_to,
                ),
            )
            conn.commit()
        return self.get_case(case_id)

    def list_cases(self, limit: int = 200) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, updated_at, status, title, event_id, players_json, summary, tags_json, priority, assigned_to "
                    "FROM cases ORDER BY updated_at DESC LIMIT ?"
                ),
                (max(1, min(limit, 500)),),
            ).fetchall()
        return [self._row_to_case(row) for row in rows]

    def get_case(self, case_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, created_at, updated_at, status, title, event_id, players_json, summary, tags_json, priority, assigned_to "
                    "FROM cases WHERE id = ?"
                ),
                (case_id,),
            ).fetchone()
        if row is None:
            raise KeyError("Case not found")
        return self._row_to_case(row)

    def update_case_status(self, case_id: str, status: str) -> dict:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE cases SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, case_id),
            )
            conn.commit()
        return self.get_case(case_id)

    def add_note(
        self,
        case_id: str,
        author: str | None,
        note_type: str | None,
        structured: dict,
        text: str | None,
    ) -> dict:
        note_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO case_notes (id, case_id, created_at, author, note_type, structured_json, text) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (note_id, case_id, now, author, note_type, json.dumps(structured or {}), text),
            )
            conn.commit()
        return {
            "id": note_id,
            "case_id": case_id,
            "created_at": now,
            "author": author,
            "note_type": note_type,
            "structured": structured or {},
            "text": text,
        }

    def list_notes(self, case_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, author, note_type, structured_json, text "
                    "FROM case_notes WHERE case_id = ? ORDER BY created_at DESC"
                ),
                (case_id,),
            ).fetchall()
        out: list[dict] = []
        for row in rows:
            note_id, created_at, author, note_type, structured_json, text = row
            out.append(
                {
                    "id": note_id,
                    "case_id": case_id,
                    "created_at": created_at,
                    "author": author,
                    "note_type": note_type,
                    "structured": json.loads(structured_json or "{}"),
                    "text": text,
                }
            )
        return out

    def add_evidence(
        self,
        case_id: str,
        evidence_type: str,
        label: str | None,
        path: str | None,
        metadata: dict,
    ) -> dict:
        evidence_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO case_evidence (id, case_id, created_at, evidence_type, label, path, metadata_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (evidence_id, case_id, now, evidence_type, label, path, json.dumps(metadata or {})),
            )
            conn.commit()
        return {
            "id": evidence_id,
            "case_id": case_id,
            "created_at": now,
            "evidence_type": evidence_type,
            "label": label,
            "path": path,
            "metadata": metadata or {},
        }

    def list_evidence(self, case_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, evidence_type, label, path, metadata_json "
                    "FROM case_evidence WHERE case_id = ? ORDER BY created_at DESC"
                ),
                (case_id,),
            ).fetchall()
        out: list[dict] = []
        for row in rows:
            evidence_id, created_at, evidence_type, label, path, metadata_json = row
            out.append(
                {
                    "id": evidence_id,
                    "case_id": case_id,
                    "created_at": created_at,
                    "evidence_type": evidence_type,
                    "label": label,
                    "path": path,
                    "metadata": json.loads(metadata_json or "{}"),
                }
            )
        return out

    def add_flag(
        self,
        case_id: str,
        flag_type: str,
        severity: str,
        message: str,
        metadata: dict,
    ) -> dict:
        flag_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO case_flags (id, case_id, created_at, flag_type, severity, message, metadata_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (flag_id, case_id, now, flag_type, severity, message, json.dumps(metadata or {})),
            )
            conn.commit()
        return {
            "id": flag_id,
            "case_id": case_id,
            "created_at": now,
            "flag_type": flag_type,
            "severity": severity,
            "message": message,
            "metadata": metadata or {},
        }

    def list_flags(self, case_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, flag_type, severity, message, metadata_json "
                    "FROM case_flags WHERE case_id = ? ORDER BY created_at DESC"
                ),
                (case_id,),
            ).fetchall()
        out: list[dict] = []
        for row in rows:
            flag_id, created_at, flag_type, severity, message, metadata_json = row
            out.append(
                {
                    "id": flag_id,
                    "case_id": case_id,
                    "created_at": created_at,
                    "flag_type": flag_type,
                    "severity": severity,
                    "message": message,
                    "metadata": json.loads(metadata_json or "{}"),
                }
            )
        return out

    def add_report(
        self,
        case_id: str | None,
        audit_id: str | None,
        report_type: str,
        mode: str,
        fmt: str,
        content: dict,
        content_text: str | None = None,
    ) -> dict:
        report_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO case_reports (id, case_id, audit_id, created_at, report_type, mode, format, content_json, content_text) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (report_id, case_id, audit_id, now, report_type, mode, fmt, json.dumps(content), content_text),
            )
            conn.commit()
        return self.get_report(report_id)

    def add_review(
        self,
        case_id: str,
        reviewer_user_id: str | None,
        action: str,
        rationale: str | None,
        payload: dict,
    ) -> dict:
        review_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO case_reviews (id, case_id, reviewer_user_id, action, rationale, payload_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (review_id, case_id, reviewer_user_id, action, rationale, json.dumps(payload or {}), now),
            )
            conn.commit()
        return {
            "id": review_id,
            "case_id": case_id,
            "reviewer_user_id": reviewer_user_id,
            "action": action,
            "rationale": rationale,
            "payload": payload or {},
            "created_at": now,
        }

    def list_reviews(self, case_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, reviewer_user_id, action, rationale, payload_json, created_at "
                    "FROM case_reviews WHERE case_id = ? ORDER BY created_at DESC"
                ),
                (case_id,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "case_id": case_id,
                "reviewer_user_id": row[1],
                "action": row[2],
                "rationale": row[3],
                "payload": json.loads(row[4] or "{}"),
                "created_at": row[5],
            }
            for row in rows
        ]

    def add_signoff(
        self,
        case_id: str,
        signer_user_id: str | None,
        signer_role: str,
        decision: str,
        note: str | None,
    ) -> dict:
        signoff_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO case_signoffs (id, case_id, signer_user_id, signer_role, decision, note, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (signoff_id, case_id, signer_user_id, signer_role, decision, note, now),
            )
            conn.commit()
        return {
            "id": signoff_id,
            "case_id": case_id,
            "signer_user_id": signer_user_id,
            "signer_role": signer_role,
            "decision": decision,
            "note": note,
            "created_at": now,
        }

    def list_signoffs(self, case_id: str) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, signer_user_id, signer_role, decision, note, created_at "
                    "FROM case_signoffs WHERE case_id = ? ORDER BY created_at DESC"
                ),
                (case_id,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "case_id": case_id,
                "signer_user_id": row[1],
                "signer_role": row[2],
                "decision": row[3],
                "note": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]

    def get_report(self, report_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, case_id, audit_id, created_at, report_type, mode, format, content_json, content_text "
                    "FROM case_reports WHERE id = ?"
                ),
                (report_id,),
            ).fetchone()
        if row is None:
            raise KeyError("Report not found")
        report_id, case_id, audit_id, created_at, report_type, mode, fmt, content_json, content_text = row
        return {
            "id": report_id,
            "case_id": case_id,
            "audit_id": audit_id,
            "created_at": created_at,
            "report_type": report_type,
            "mode": mode,
            "format": fmt,
            "content": json.loads(content_json or "{}"),
            "content_text": content_text,
        }

    def create_live_session(self, event_id: str | None, players: list[str]) -> dict:
        session_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO live_sessions (id, created_at, updated_at, event_id, players_json, status) "
                    "VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (session_id, now, now, event_id, json.dumps(players), "active"),
            )
            conn.commit()
        return self.get_live_session(session_id)

    def get_live_session(self, session_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, created_at, updated_at, event_id, players_json, status "
                    "FROM live_sessions WHERE id = ?"
                ),
                (session_id,),
            ).fetchone()
        if row is None:
            raise KeyError("Live session not found")
        session_id, created_at, updated_at, event_id, players_json, status = row
        return {
            "id": session_id,
            "created_at": created_at,
            "updated_at": updated_at,
            "event_id": event_id,
            "players": json.loads(players_json or "[]"),
            "status": status,
        }

    def add_live_move(
        self,
        session_id: str,
        ply: int,
        move_uci: str,
        time_spent: float | None,
        clock_remaining: float | None,
        complexity: float | None,
        engine_match: float | None,
        maia_prob: float | None,
        tags: dict,
    ) -> dict:
        move_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO live_moves (id, session_id, created_at, ply, move_uci, time_spent, clock_remaining, complexity, engine_match, maia_prob, tags_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    move_id,
                    session_id,
                    now,
                    ply,
                    move_uci,
                    time_spent,
                    clock_remaining,
                    complexity,
                    engine_match,
                    maia_prob,
                    json.dumps(tags or {}),
                ),
            )
            conn.execute(
                "UPDATE live_sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            conn.commit()
        return {
            "id": move_id,
            "session_id": session_id,
            "created_at": now,
            "ply": ply,
            "move_uci": move_uci,
            "time_spent": time_spent,
            "clock_remaining": clock_remaining,
            "complexity": complexity,
            "engine_match": engine_match,
            "maia_prob": maia_prob,
            "tags": tags or {},
        }

    def list_live_moves(self, session_id: str, limit: int = 200) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, ply, move_uci, time_spent, clock_remaining, complexity, engine_match, maia_prob, tags_json "
                    "FROM live_moves WHERE session_id = ? ORDER BY ply DESC LIMIT ?"
                ),
                (session_id, max(1, min(limit, 500))),
            ).fetchall()
        out: list[dict] = []
        for row in rows:
            move_id, created_at, ply, move_uci, time_spent, clock_remaining, complexity, engine_match, maia_prob, tags_json = row
            out.append(
                {
                    "id": move_id,
                    "session_id": session_id,
                    "created_at": created_at,
                    "ply": ply,
                    "move_uci": move_uci,
                    "time_spent": time_spent,
                    "clock_remaining": clock_remaining,
                    "complexity": complexity,
                    "engine_match": engine_match,
                    "maia_prob": maia_prob,
                    "tags": json.loads(tags_json or "{}"),
                }
            )
        return out

    def upsert_player_profile(self, player_id: str, profile: dict) -> dict:
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO player_profiles (player_id, updated_at, profile_json) "
                    "VALUES (?, ?, ?) "
                    "ON CONFLICT(player_id) DO UPDATE SET updated_at = excluded.updated_at, profile_json = excluded.profile_json"
                ),
                (player_id, now, json.dumps(profile)),
            )
            conn.commit()
        return {"player_id": player_id, "updated_at": now, "profile": profile}

    def get_player_profile(self, player_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT player_id, updated_at, profile_json FROM player_profiles WHERE player_id = ?",
                (player_id,),
            ).fetchone()
        if row is None:
            return None
        pid, updated_at, profile_json = row
        return {"player_id": pid, "updated_at": updated_at, "profile": json.loads(profile_json or "{}")}

    def add_player_history(self, player_id: str, event_id: str | None, snapshot: dict) -> dict:
        hist_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO player_history (id, player_id, created_at, event_id, snapshot_json) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (hist_id, player_id, now, event_id, json.dumps(snapshot)),
            )
            conn.commit()
        return {"id": hist_id, "player_id": player_id, "created_at": now, "event_id": event_id, "snapshot": snapshot}

    def list_player_history(self, player_id: str, limit: int = 200) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, created_at, event_id, snapshot_json "
                    "FROM player_history WHERE player_id = ? ORDER BY created_at DESC LIMIT ?"
                ),
                (player_id, max(1, min(limit, 500))),
            ).fetchall()
        out: list[dict] = []
        for row in rows:
            hist_id, created_at, event_id, snapshot_json = row
            out.append(
                {
                    "id": hist_id,
                    "player_id": player_id,
                    "created_at": created_at,
                    "event_id": event_id,
                    "snapshot": json.loads(snapshot_json or "{}"),
                }
            )
        return out

    def add_otb_incident(
        self,
        case_id: str | None,
        event_id: str | None,
        player_id: str | None,
        incident_type: str,
        severity: str,
        description: str | None,
        occurred_at: str | None,
        metadata: dict,
    ) -> dict:
        incident_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO otb_incidents (id, case_id, event_id, player_id, incident_type, severity, description, occurred_at, metadata_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    incident_id,
                    case_id,
                    event_id,
                    player_id,
                    incident_type,
                    severity,
                    description,
                    occurred_at,
                    json.dumps(metadata or {}),
                    now,
                ),
            )
            conn.commit()
        return self.get_otb_incident(incident_id)

    def get_otb_incident(self, incident_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, case_id, event_id, player_id, incident_type, severity, description, occurred_at, metadata_json, created_at "
                    "FROM otb_incidents WHERE id = ?"
                ),
                (incident_id,),
            ).fetchone()
        if row is None:
            raise KeyError("OTB incident not found")
        return self._row_to_otb_incident(row)

    def list_otb_incidents(self, case_id: str | None = None, event_id: str | None = None) -> list[dict]:
        query = (
            "SELECT id, case_id, event_id, player_id, incident_type, severity, description, occurred_at, metadata_json, created_at "
            "FROM otb_incidents"
        )
        params: list[str] = []
        clauses: list[str] = []
        if case_id:
            clauses.append("case_id = ?")
            params.append(case_id)
        if event_id:
            clauses.append("event_id = ?")
            params.append(event_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_otb_incident(row) for row in rows]

    @staticmethod
    def _row_to_otb_incident(row: tuple) -> dict:
        (
            incident_id,
            case_id,
            event_id,
            player_id,
            incident_type,
            severity,
            description,
            occurred_at,
            metadata_json,
            created_at,
        ) = row
        metadata = {}
        if metadata_json:
            try:
                metadata = json.loads(metadata_json)
            except Exception:
                metadata = {}
        return {
            "id": incident_id,
            "case_id": case_id,
            "event_id": event_id,
            "player_id": player_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "occurred_at": occurred_at,
            "metadata": metadata,
            "created_at": created_at,
        }

    def add_otb_camera_event(
        self,
        event_id: str | None,
        case_id: str | None,
        player_id: str | None,
        session_id: str | None,
        camera_id: str | None,
        storage_mode: str,
        consent: dict,
        events: list[dict],
        summary: dict,
    ) -> dict:
        cam_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO otb_camera_events (id, event_id, case_id, player_id, session_id, camera_id, storage_mode, consent_json, events_json, summary_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    cam_id,
                    event_id,
                    case_id,
                    player_id,
                    session_id,
                    camera_id,
                    storage_mode,
                    json.dumps(consent or {}),
                    json.dumps(events or []),
                    json.dumps(summary or {}),
                    now,
                ),
            )
            conn.commit()
        return {"id": cam_id, "created_at": now}

    def add_dgt_board_event(
        self,
        event_id: str | None,
        session_id: str | None,
        board_serial: str | None,
        move_uci: str | None,
        ply: int | None,
        fen: str | None,
        clock_ms: int | None,
        raw: dict,
    ) -> dict:
        evt_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO dgt_board_events (id, event_id, session_id, board_serial, move_uci, ply, fen, clock_ms, raw_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    evt_id,
                    event_id,
                    session_id,
                    board_serial,
                    move_uci,
                    ply,
                    fen,
                    clock_ms,
                    json.dumps(raw or {}),
                    now,
                ),
            )
            conn.commit()
        return {"id": evt_id, "created_at": now}

    def list_otb_camera_events(
        self,
        event_id: str | None = None,
        case_id: str | None = None,
        player_id: str | None = None,
        session_id: str | None = None,
        limit: int = 200,
    ) -> list[dict]:
        query = (
            "SELECT id, event_id, case_id, player_id, session_id, camera_id, storage_mode, consent_json, events_json, summary_json, created_at "
            "FROM otb_camera_events"
        )
        params: list[str | int] = []
        clauses: list[str] = []
        if event_id:
            clauses.append("event_id = ?")
            params.append(event_id)
        if case_id:
            clauses.append("case_id = ?")
            params.append(case_id)
        if player_id:
            clauses.append("player_id = ?")
            params.append(player_id)
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        out: list[dict] = []
        for row in rows:
            (
                cam_id,
                ev_id,
                cs_id,
                pl_id,
                sess_id,
                camera_id,
                storage_mode,
                consent_json,
                events_json,
                summary_json,
                created_at,
            ) = row
            out.append(
                {
                    "id": cam_id,
                    "event_id": ev_id,
                    "case_id": cs_id,
                    "player_id": pl_id,
                    "session_id": sess_id,
                    "camera_id": camera_id,
                    "storage_mode": storage_mode,
                    "consent": json.loads(consent_json or "{}"),
                    "events": json.loads(events_json or "[]"),
                    "summary": json.loads(summary_json or "{}"),
                    "created_at": created_at,
                }
            )
        return out

    def list_dgt_board_events(
        self,
        event_id: str | None = None,
        session_id: str | None = None,
        limit: int = 200,
    ) -> list[dict]:
        query = (
            "SELECT id, event_id, session_id, board_serial, move_uci, ply, fen, clock_ms, raw_json, created_at "
            "FROM dgt_board_events"
        )
        params: list[str | int] = []
        clauses: list[str] = []
        if event_id:
            clauses.append("event_id = ?")
            params.append(event_id)
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, params).fetchall()
        out: list[dict] = []
        for row in rows:
            (
                evt_id,
                ev_id,
                sess_id,
                board_serial,
                move_uci,
                ply,
                fen,
                clock_ms,
                raw_json,
                created_at,
            ) = row
            out.append(
                {
                    "id": evt_id,
                    "event_id": ev_id,
                    "session_id": sess_id,
                    "board_serial": board_serial,
                    "move_uci": move_uci,
                    "ply": ply,
                    "fen": fen,
                    "clock_ms": clock_ms,
                    "raw": json.loads(raw_json or "{}"),
                    "created_at": created_at,
                }
            )
        return out

    @staticmethod
    def _row_to_case(row: tuple) -> dict:
        (
            case_id,
            created_at,
            updated_at,
            status,
            title,
            event_id,
            players_json,
            summary,
            tags_json,
            priority,
            assigned_to,
        ) = row
        return {
            "id": case_id,
            "created_at": created_at,
            "updated_at": updated_at,
            "status": status,
            "title": title,
            "event_id": event_id,
            "players": json.loads(players_json or "[]"),
            "summary": summary,
            "tags": json.loads(tags_json or "[]"),
            "priority": priority,
            "assigned_to": assigned_to,
        }
