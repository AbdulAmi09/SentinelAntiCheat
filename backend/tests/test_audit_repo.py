from __future__ import annotations

from pathlib import Path
import pytest

from sentinel.repositories.audit import AuditRepository


def test_audit_recent_filters_by_event(tmp_path: Path) -> None:
    db = tmp_path / "audit_test.db"
    repo = AuditRepository(str(db))

    repo.write(
        {
            "request": {"player_id": "p1", "event_id": "evt-1"},
            "response": {"risk_tier": "LOW", "signals": []},
        },
        model_version="v-test",
    )
    repo.write(
        {
            "request": {"player_id": "p2", "event_id": "evt-2"},
            "response": {"risk_tier": "ELEVATED", "signals": []},
        },
        model_version="v-test",
    )

    all_rows = repo.recent(limit=10)
    evt1_rows = repo.recent(limit=10, event_id="evt-1")

    assert len(all_rows) == 2
    assert len(evt1_rows) == 1
    assert evt1_rows[0]["request"]["event_id"] == "evt-1"
    assert all_rows[0]["chain_hash"] is not None
    assert all_rows[1]["chain_hash"] is not None


def test_report_workflow_lock_and_version(tmp_path: Path) -> None:
    db = tmp_path / "audit_report.db"
    repo = AuditRepository(str(db))

    audit_id = repo.write(
        {
            "request": {"player_id": "p1", "event_id": "evt-1"},
            "response": {"risk_tier": "LOW", "signals": []},
        },
        model_version="v-test",
    )

    state1 = repo.get_report_workflow(audit_id)
    assert state1["report_version"] == 1
    assert state1["report_locked"] is False

    state2 = repo.bump_report_version(audit_id)
    assert state2["report_version"] == 2
    assert state2["report_locked"] is False

    state3 = repo.lock_report(audit_id)
    assert state3["report_locked"] is True
    assert state3["report_locked_at"] is not None

    with pytest.raises(ValueError):
        repo.bump_report_version(audit_id)


def test_batch_run_persistence(tmp_path: Path) -> None:
    db = tmp_path / "audit_batch.db"
    repo = AuditRepository(str(db))

    run = repo.create_batch_run(
        event_id="evt-batch",
        source_name="sample.pgn",
        request_payload={"max_games": 10},
    )
    assert run["status"] == "queued"

    completed = repo.complete_batch_run(
        run["id"],
        response_payload={"analyses_generated": 3},
        csv_text="Name,Rating\np1,1800\n",
    )
    assert completed["status"] == "completed"
    assert completed["response"]["analyses_generated"] == 3
    assert "Name,Rating" in (completed["csv_text"] or "")

    listed = repo.list_batch_runs(limit=10)
    assert listed[0]["id"] == run["id"]
