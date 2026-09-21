from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sentinel.services.crypto import decrypt_text, encrypt_text, hash_key


class PartnerRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._ensure()

    def _ensure(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS partner_api_keys (
                  id TEXT PRIMARY KEY,
                  key TEXT NOT NULL,
                  key_hash TEXT,
                  secret TEXT NOT NULL,
                  partner_name TEXT NOT NULL,
                  webhook_url TEXT,
                  rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
                  active INTEGER NOT NULL DEFAULT 1,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS partner_jobs (
                  id TEXT PRIMARY KEY,
                  job_id TEXT NOT NULL,
                  api_key_id TEXT NOT NULL,
                  game_id TEXT NOT NULL,
                  player_id TEXT NOT NULL,
                  raw_payload_json TEXT NOT NULL,
                  status TEXT NOT NULL,
                  risk_level TEXT,
                  risk_score REAL,
                  result_json TEXT,
                  webhook_url TEXT,
                  webhook_delivered INTEGER NOT NULL DEFAULT 0,
                  webhook_attempts INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL,
                  completed_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS partner_sessions (
                  id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  api_key_id TEXT NOT NULL,
                  game_id TEXT,
                  player_id TEXT,
                  status TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  ended_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS device_fingerprints (
                  fingerprint_hash TEXT PRIMARY KEY,
                  first_seen TEXT NOT NULL,
                  last_seen TEXT NOT NULL,
                  last_player_id TEXT,
                  seen_count INTEGER NOT NULL DEFAULT 1,
                  distinct_players_json TEXT NOT NULL,
                  metadata_json TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS camera_events (
                  id TEXT PRIMARY KEY,
                  job_id TEXT NOT NULL,
                  mode TEXT NOT NULL,
                  events_json TEXT NOT NULL,
                  consent_json TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consent_logs (
                  id TEXT PRIMARY KEY,
                  job_id TEXT NOT NULL,
                  api_key_id TEXT NOT NULL,
                  consent_type TEXT NOT NULL,
                  consent_given INTEGER NOT NULL,
                  metadata_json TEXT,
                  created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
            self._ensure_key_hash_column(conn)
<<<<<<< HEAD
            self._ensure_partner_scope_columns(conn)
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            self._backfill_key_hashes(conn)

    def _ensure_key_hash_column(self, conn: sqlite3.Connection) -> None:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(partner_api_keys)").fetchall()}
        if "key_hash" not in columns:
            conn.execute("ALTER TABLE partner_api_keys ADD COLUMN key_hash TEXT")
            conn.commit()

    def _backfill_key_hashes(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute("SELECT id, key, key_hash FROM partner_api_keys").fetchall()
        for row in rows:
            key_id, key_value, key_hash_value = row
            if key_hash_value:
                continue
            try:
                plain = decrypt_text(key_value)
            except Exception:
                plain = key_value
            if not plain:
                continue
            conn.execute(
                "UPDATE partner_api_keys SET key_hash = ? WHERE id = ?",
                (hash_key(plain), key_id),
            )
        conn.commit()

<<<<<<< HEAD
    def _ensure_partner_scope_columns(self, conn: sqlite3.Connection) -> None:
        table_columns = {
            table_name: {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}
            for table_name in ("partner_api_keys", "partner_jobs", "partner_sessions")
        }
        if "federation_id" not in table_columns["partner_api_keys"]:
            conn.execute("ALTER TABLE partner_api_keys ADD COLUMN federation_id TEXT")
        if "federation_id" not in table_columns["partner_jobs"]:
            conn.execute("ALTER TABLE partner_jobs ADD COLUMN federation_id TEXT")
        if "federation_id" not in table_columns["partner_sessions"]:
            conn.execute("ALTER TABLE partner_sessions ADD COLUMN federation_id TEXT")
        conn.execute(
            """
            UPDATE partner_jobs
            SET federation_id = (
              SELECT pak.federation_id
              FROM partner_api_keys pak
              WHERE pak.id = partner_jobs.api_key_id
            )
            WHERE federation_id IS NULL
            """
        )
        conn.execute(
            """
            UPDATE partner_sessions
            SET federation_id = (
              SELECT pak.federation_id
              FROM partner_api_keys pak
              WHERE pak.id = partner_sessions.api_key_id
            )
            WHERE federation_id IS NULL
            """
        )
        conn.commit()

=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    def create_key(
        self,
        key: str,
        secret: str,
        partner_name: str,
<<<<<<< HEAD
        federation_id: str | None,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        webhook_url: str | None,
        rate_limit_per_minute: int,
    ) -> dict:
        key_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        key_hash = hash_key(key)
        key_enc = encrypt_text(key)
        secret_enc = encrypt_text(secret)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
<<<<<<< HEAD
                    "INSERT INTO partner_api_keys (id, key, key_hash, secret, partner_name, federation_id, webhook_url, rate_limit_per_minute, active, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)"
                ),
                (key_id, key_enc, key_hash, secret_enc, partner_name, federation_id, webhook_url, rate_limit_per_minute, now),
=======
                    "INSERT INTO partner_api_keys (id, key, key_hash, secret, partner_name, webhook_url, rate_limit_per_minute, active, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)"
                ),
                (key_id, key_enc, key_hash, secret_enc, partner_name, webhook_url, rate_limit_per_minute, now),
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            )
            conn.commit()
        return self.get_key(key_id, reveal=True)

<<<<<<< HEAD
    def list_keys(self, federation_id: str | None = None) -> list[dict]:
        query = (
            "SELECT id, key, secret, partner_name, federation_id, webhook_url, rate_limit_per_minute, active, created_at "
            "FROM partner_api_keys "
        )
        params: list[object] = []
        if federation_id:
            query += "WHERE federation_id = ? "
            params.append(federation_id)
        query += "ORDER BY created_at DESC"
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [self._row_to_key(row, reveal=False) for row in rows]

    def get_key(self, key_id: str, reveal: bool = False, federation_id: str | None = None) -> dict:
        query = (
            "SELECT id, key, secret, partner_name, federation_id, webhook_url, rate_limit_per_minute, active, created_at "
            "FROM partner_api_keys WHERE id = ?"
        )
        params: list[object] = [key_id]
        if federation_id:
            query += " AND federation_id = ?"
            params.append(federation_id)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(query, tuple(params)).fetchone()
=======
    def list_keys(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                (
                    "SELECT id, key, secret, partner_name, webhook_url, rate_limit_per_minute, active, created_at "
                    "FROM partner_api_keys ORDER BY created_at DESC"
                )
            ).fetchall()
        return [self._row_to_key(row, reveal=False) for row in rows]

    def get_key(self, key_id: str, reveal: bool = False) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT id, key, secret, partner_name, webhook_url, rate_limit_per_minute, active, created_at "
                    "FROM partner_api_keys WHERE id = ?"
                ),
                (key_id,),
            ).fetchone()
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        if row is None:
            raise KeyError("Partner key not found")
        return self._row_to_key(row, reveal=reveal)

    def find_key(self, api_key: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
<<<<<<< HEAD
                    "SELECT id, key, secret, partner_name, federation_id, webhook_url, rate_limit_per_minute, active, created_at "
=======
                    "SELECT id, key, secret, partner_name, webhook_url, rate_limit_per_minute, active, created_at "
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                    "FROM partner_api_keys WHERE key_hash = ? AND active = 1"
                ),
                (hash_key(api_key),),
            ).fetchone()
            if row is None:
                rows = conn.execute(
                    (
<<<<<<< HEAD
                        "SELECT id, key, secret, partner_name, federation_id, webhook_url, rate_limit_per_minute, active, created_at "
=======
                        "SELECT id, key, secret, partner_name, webhook_url, rate_limit_per_minute, active, created_at "
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                        "FROM partner_api_keys WHERE active = 1"
                    )
                ).fetchall()
                for legacy in rows:
                    try:
                        legacy_key = decrypt_text(legacy[1])
                    except Exception:
                        legacy_key = legacy[1]
                    if legacy_key == api_key:
                        row = legacy
                        break
        if row is None:
            return None
        return self._row_to_key(row, reveal=False)

<<<<<<< HEAD
    def update_webhook(self, key_id: str, webhook_url: str | None, federation_id: str | None = None) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            if federation_id:
                conn.execute(
                    "UPDATE partner_api_keys SET webhook_url = ? WHERE id = ? AND federation_id = ?",
                    (webhook_url, key_id, federation_id),
                )
            else:
                conn.execute(
                    "UPDATE partner_api_keys SET webhook_url = ? WHERE id = ?",
                    (webhook_url, key_id),
                )
            conn.commit()
        return self.get_key(key_id, federation_id=federation_id)

    def disable_key(self, key_id: str, federation_id: str | None = None) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            if federation_id:
                conn.execute("UPDATE partner_api_keys SET active = 0 WHERE id = ? AND federation_id = ?", (key_id, federation_id))
            else:
                conn.execute("UPDATE partner_api_keys SET active = 0 WHERE id = ?", (key_id,))
            conn.commit()
        return self.get_key(key_id, federation_id=federation_id)

    def rotate_secret(self, key_id: str, new_secret: str, federation_id: str | None = None) -> dict:
        secret_enc = encrypt_text(new_secret)
        with sqlite3.connect(self.db_path) as conn:
            if federation_id:
                conn.execute(
                    "UPDATE partner_api_keys SET secret = ? WHERE id = ? AND federation_id = ?",
                    (secret_enc, key_id, federation_id),
                )
            else:
                conn.execute("UPDATE partner_api_keys SET secret = ? WHERE id = ?", (secret_enc, key_id))
            conn.commit()
        return self.get_key(key_id, reveal=True, federation_id=federation_id)

    def rotate_keypair(self, key_id: str, new_key: str, new_secret: str, federation_id: str | None = None) -> dict:
        key_enc = encrypt_text(new_key)
        secret_enc = encrypt_text(new_secret)
        key_hash = hash_key(new_key)
        with sqlite3.connect(self.db_path) as conn:
            if federation_id:
                conn.execute(
                    "UPDATE partner_api_keys SET key = ?, key_hash = ?, secret = ? WHERE id = ? AND federation_id = ?",
                    (key_enc, key_hash, secret_enc, key_id, federation_id),
                )
            else:
                conn.execute(
                    "UPDATE partner_api_keys SET key = ?, key_hash = ?, secret = ? WHERE id = ?",
                    (key_enc, key_hash, secret_enc, key_id),
                )
            conn.commit()
        return self.get_key(key_id, reveal=True, federation_id=federation_id)
=======
    def update_webhook(self, key_id: str, webhook_url: str | None) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE partner_api_keys SET webhook_url = ? WHERE id = ?",
                (webhook_url, key_id),
            )
            conn.commit()
        return self.get_key(key_id)

    def disable_key(self, key_id: str) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE partner_api_keys SET active = 0 WHERE id = ?", (key_id,))
            conn.commit()
        return self.get_key(key_id)

    def rotate_secret(self, key_id: str, new_secret: str) -> dict:
        secret_enc = encrypt_text(new_secret)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE partner_api_keys SET secret = ? WHERE id = ?", (secret_enc, key_id))
            conn.commit()
        return self.get_key(key_id, reveal=True)
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674

    def create_job(
        self,
        job_id: str,
        api_key_id: str,
<<<<<<< HEAD
        federation_id: str | None,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        game_id: str,
        player_id: str,
        raw_payload: dict,
        webhook_url: str | None,
    ) -> dict:
        row_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
<<<<<<< HEAD
                    "INSERT INTO partner_jobs (id, job_id, api_key_id, federation_id, game_id, player_id, raw_payload_json, status, webhook_url, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)"
                ),
                (row_id, job_id, api_key_id, federation_id, game_id, player_id, json.dumps(raw_payload), webhook_url, now),
=======
                    "INSERT INTO partner_jobs (id, job_id, api_key_id, game_id, player_id, raw_payload_json, status, webhook_url, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'queued', ?, ?)"
                ),
                (row_id, job_id, api_key_id, game_id, player_id, json.dumps(raw_payload), webhook_url, now),
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            )
            conn.commit()
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT job_id, api_key_id, game_id, player_id, raw_payload_json, status, risk_level, risk_score, "
<<<<<<< HEAD
                    "result_json, webhook_url, webhook_delivered, webhook_attempts, created_at, completed_at, federation_id "
=======
                    "result_json, webhook_url, webhook_delivered, webhook_attempts, created_at, completed_at "
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
                    "FROM partner_jobs WHERE job_id = ?"
                ),
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        (
            job_id,
            api_key_id,
            game_id,
            player_id,
            raw_payload_json,
            status,
            risk_level,
            risk_score,
            result_json,
            webhook_url,
            webhook_delivered,
            webhook_attempts,
            created_at,
            completed_at,
<<<<<<< HEAD
            federation_id,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        ) = row
        return {
            "job_id": job_id,
            "api_key_id": api_key_id,
<<<<<<< HEAD
            "federation_id": federation_id,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            "game_id": game_id,
            "player_id": player_id,
            "raw_payload": json.loads(raw_payload_json or "{}"),
            "status": status,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "result": json.loads(result_json or "{}") if result_json else None,
            "webhook_url": webhook_url,
            "webhook_delivered": bool(webhook_delivered),
            "webhook_attempts": int(webhook_attempts or 0),
            "created_at": created_at,
            "completed_at": completed_at,
        }

    def update_job_result(
        self,
        job_id: str,
        status: str,
        risk_level: str | None,
        risk_score: float | None,
        result: dict | None,
        webhook_attempts: int,
        webhook_delivered: bool,
    ) -> dict:
        completed_at = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "UPDATE partner_jobs SET status = ?, risk_level = ?, risk_score = ?, result_json = ?, "
                    "webhook_attempts = ?, webhook_delivered = ?, completed_at = ? WHERE job_id = ?"
                ),
                (
                    status,
                    risk_level,
                    risk_score,
                    json.dumps(result) if result is not None else None,
                    webhook_attempts,
                    1 if webhook_delivered else 0,
                    completed_at,
                    job_id,
                ),
            )
            conn.commit()
        return self.get_job(job_id) or {}

    def record_device_fingerprint(
        self,
        fingerprint_hash: str,
        player_id: str | None,
        metadata: dict | None,
    ) -> dict:
        if not fingerprint_hash:
            return {
                "fingerprint_hash": "",
                "seen_count": 0,
                "distinct_players": [],
                "distinct_count": 0,
            }
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                (
                    "SELECT fingerprint_hash, first_seen, last_seen, last_player_id, seen_count, distinct_players_json "
                    "FROM device_fingerprints WHERE fingerprint_hash = ?"
                ),
                (fingerprint_hash,),
            ).fetchone()
            if row is None:
                distinct = [player_id] if player_id else []
                conn.execute(
                    (
                        "INSERT INTO device_fingerprints (fingerprint_hash, first_seen, last_seen, last_player_id, seen_count, distinct_players_json, metadata_json) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)"
                    ),
                    (
                        fingerprint_hash,
                        now,
                        now,
                        player_id,
                        1,
                        json.dumps(distinct),
                        json.dumps(metadata or {}),
                    ),
                )
                conn.commit()
                return {
                    "fingerprint_hash": fingerprint_hash,
                    "seen_count": 1,
                    "distinct_players": distinct,
                    "distinct_count": len(distinct),
                }

            _, first_seen, _, _, seen_count, distinct_json = row
            distinct = json.loads(distinct_json or "[]")
            if player_id and player_id not in distinct:
                distinct.append(player_id)
            conn.execute(
                (
                    "UPDATE device_fingerprints SET last_seen = ?, last_player_id = ?, seen_count = ?, distinct_players_json = ?, metadata_json = ? "
                    "WHERE fingerprint_hash = ?"
                ),
                (
                    now,
                    player_id,
                    int(seen_count) + 1,
                    json.dumps(distinct),
                    json.dumps(metadata or {}),
                    fingerprint_hash,
                ),
            )
            conn.commit()
        return {
            "fingerprint_hash": fingerprint_hash,
            "seen_count": int(seen_count) + 1,
            "distinct_players": distinct,
            "distinct_count": len(distinct),
            "first_seen": first_seen,
            "last_seen": now,
        }

    def add_camera_events(
        self,
        job_id: str,
        mode: str,
        events: list[dict],
        consent: dict | None,
    ) -> dict:
        camera_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO camera_events (id, job_id, mode, events_json, consent_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (
                    camera_id,
                    job_id,
                    mode,
                    json.dumps(events or []),
                    json.dumps(consent or {}),
                    now,
                ),
            )
            conn.commit()
        return {"id": camera_id, "job_id": job_id, "mode": mode, "created_at": now}

    def add_consent_log(
        self,
        job_id: str,
        api_key_id: str,
        consent_type: str,
        consent_given: bool,
        metadata: dict | None,
    ) -> dict:
        consent_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
                    "INSERT INTO consent_logs (id, job_id, api_key_id, consent_type, consent_given, metadata_json, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (consent_id, job_id, api_key_id, consent_type, 1 if consent_given else 0, json.dumps(metadata or {}), now),
            )
            conn.commit()
        return {"id": consent_id, "job_id": job_id, "consent_type": consent_type, "created_at": now}

    def list_queued_jobs(self, limit: int = 50) -> list[str]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT job_id FROM partner_jobs WHERE status = 'queued' ORDER BY created_at ASC LIMIT ?",
                (max(1, min(limit, 200)),),
            ).fetchall()
        return [r[0] for r in rows if r and r[0]]

    def create_session(
        self,
        session_id: str,
        api_key_id: str,
<<<<<<< HEAD
        federation_id: str | None,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        game_id: str | None,
        player_id: str | None,
    ) -> dict:
        row_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                (
<<<<<<< HEAD
                    "INSERT INTO partner_sessions (id, session_id, api_key_id, federation_id, game_id, player_id, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'active', ?)"
                ),
                (row_id, session_id, api_key_id, federation_id, game_id, player_id, now),
            )
            conn.commit()
        return {
            "session_id": session_id,
            "api_key_id": api_key_id,
            "federation_id": federation_id,
            "game_id": game_id,
            "player_id": player_id,
        }

    def list_jobs(
        self,
        limit: int = 200,
        api_key_id: str | None = None,
        federation_id: str | None = None,
    ) -> list[dict]:
        query = (
            "SELECT job_id, api_key_id, federation_id, game_id, player_id, raw_payload_json, status, risk_level, risk_score, "
            "result_json, webhook_url, webhook_delivered, webhook_attempts, created_at, completed_at "
            "FROM partner_jobs "
        )
        params: list[object] = []
        filters: list[str] = []
        if api_key_id:
            filters.append("api_key_id = ?")
            params.append(api_key_id)
        if federation_id:
            filters.append("federation_id = ?")
            params.append(federation_id)
        if filters:
            query += "WHERE " + " AND ".join(filters) + " "
        query += "ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            if federation_id:
                key_rows = conn.execute(
                    "SELECT id, partner_name FROM partner_api_keys WHERE federation_id = ?",
                    (federation_id,),
                ).fetchall()
            else:
                key_rows = conn.execute("SELECT id, partner_name FROM partner_api_keys").fetchall()
        partner_names = {row[0]: row[1] for row in key_rows}
        jobs: list[dict] = []
        for row in rows:
            (
                job_id,
                row_api_key_id,
                row_federation_id,
                game_id,
                player_id,
                raw_payload_json,
                status,
                risk_level,
                risk_score,
                result_json,
                webhook_url,
                webhook_delivered,
                webhook_attempts,
                created_at,
                completed_at,
            ) = row
            jobs.append(
                {
                    "job_id": job_id,
                    "api_key_id": row_api_key_id,
                    "federation_id": row_federation_id,
                    "partner_name": partner_names.get(row_api_key_id),
                    "game_id": game_id,
                    "player_id": player_id,
                    "raw_payload": json.loads(raw_payload_json or "{}"),
                    "status": status,
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "result": json.loads(result_json or "{}") if result_json else None,
                    "webhook_url": webhook_url,
                    "webhook_delivered": bool(webhook_delivered),
                    "webhook_attempts": int(webhook_attempts or 0),
                    "created_at": created_at,
                    "completed_at": completed_at,
                }
            )
        return jobs

    def list_sessions(
        self,
        limit: int = 200,
        api_key_id: str | None = None,
        federation_id: str | None = None,
    ) -> list[dict]:
        query = (
            "SELECT session_id, api_key_id, federation_id, game_id, player_id, status, created_at, ended_at "
            "FROM partner_sessions "
        )
        params: list[object] = []
        filters: list[str] = []
        if api_key_id:
            filters.append("api_key_id = ?")
            params.append(api_key_id)
        if federation_id:
            filters.append("federation_id = ?")
            params.append(federation_id)
        if filters:
            query += "WHERE " + " AND ".join(filters) + " "
        query += "ORDER BY created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            if federation_id:
                key_rows = conn.execute(
                    "SELECT id, partner_name FROM partner_api_keys WHERE federation_id = ?",
                    (federation_id,),
                ).fetchall()
            else:
                key_rows = conn.execute("SELECT id, partner_name FROM partner_api_keys").fetchall()
        partner_names = {row[0]: row[1] for row in key_rows}
        sessions: list[dict] = []
        for row in rows:
            session_id, row_api_key_id, row_federation_id, game_id, player_id, status, created_at, ended_at = row
            sessions.append(
                {
                    "session_id": session_id,
                    "api_key_id": row_api_key_id,
                    "federation_id": row_federation_id,
                    "partner_name": partner_names.get(row_api_key_id),
                    "game_id": game_id,
                    "player_id": player_id,
                    "status": status,
                    "created_at": created_at,
                    "ended_at": ended_at,
                }
            )
        return sessions
=======
                    "INSERT INTO partner_sessions (id, session_id, api_key_id, game_id, player_id, status, created_at) "
                    "VALUES (?, ?, ?, ?, ?, 'active', ?)"
                ),
                (row_id, session_id, api_key_id, game_id, player_id, now),
            )
            conn.commit()
        return {"session_id": session_id, "api_key_id": api_key_id, "game_id": game_id, "player_id": player_id}
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674

    @staticmethod
    def _mask(value: str | None) -> str | None:
        if not value:
            return value
        if len(value) <= 6:
            return "*" * len(value)
        return f"{'*' * (len(value) - 4)}{value[-4:]}"

    def _row_to_key(self, row: tuple, reveal: bool = False) -> dict:
<<<<<<< HEAD
        key_id, key, secret, partner_name, federation_id, webhook_url, rate_limit, active, created_at = row
=======
        key_id, key, secret, partner_name, webhook_url, rate_limit, active, created_at = row
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
        key_plain = decrypt_text(key)
        secret_plain = decrypt_text(secret)
        if reveal:
            key_value = key_plain
            secret_value = secret_plain
        else:
            key_value = self._mask(key_plain)
            secret_value = self._mask(secret_plain)
        return {
            "id": key_id,
            "key": key_value,
            "secret": secret_value,
            "partner_name": partner_name,
<<<<<<< HEAD
            "federation_id": federation_id,
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
            "webhook_url": webhook_url,
            "rate_limit_per_minute": int(rate_limit),
            "active": bool(active),
            "created_at": created_at,
            "key_last4": key_plain[-4:] if key_plain else None,
            "secret_last4": secret_plain[-4:] if secret_plain else None,
        }
