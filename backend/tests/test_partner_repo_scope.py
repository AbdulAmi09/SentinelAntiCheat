from __future__ import annotations

from pathlib import Path

from sentinel.repositories.partner import PartnerRepository


def test_partner_keys_are_scoped_by_federation(tmp_path: Path) -> None:
    repo = PartnerRepository(str(tmp_path / "partner.db"))

    alpha = repo.create_key(
        key="alpha-key",
        secret="alpha-secret",
        partner_name="Alpha Partner",
        federation_id="fed_alpha",
        webhook_url=None,
        rate_limit_per_minute=60,
    )
    repo.create_key(
        key="beta-key",
        secret="beta-secret",
        partner_name="Beta Partner",
        federation_id="fed_beta",
        webhook_url=None,
        rate_limit_per_minute=60,
    )

    alpha_keys = repo.list_keys(federation_id="fed_alpha")
    assert len(alpha_keys) == 1
    assert alpha_keys[0]["id"] == alpha["id"]
    assert alpha_keys[0]["federation_id"] == "fed_alpha"

    scoped = repo.get_key(alpha["id"], federation_id="fed_alpha")
    assert scoped["federation_id"] == "fed_alpha"


def test_partner_jobs_and_sessions_inherit_federation_scope(tmp_path: Path) -> None:
    repo = PartnerRepository(str(tmp_path / "partner.db"))
    key = repo.create_key(
        key="alpha-key",
        secret="alpha-secret",
        partner_name="Alpha Partner",
        federation_id="fed_alpha",
        webhook_url="https://alpha.test/webhook",
        rate_limit_per_minute=60,
    )

    repo.create_job(
        job_id="job-alpha",
        api_key_id=key["id"],
        federation_id=key["federation_id"],
        game_id="game-1",
        player_id="player-1",
        raw_payload={"pgn": "1. e4 e5"},
        webhook_url="https://alpha.test/webhook",
    )
    repo.create_session(
        session_id="sess-alpha",
        api_key_id=key["id"],
        federation_id=key["federation_id"],
        game_id="game-1",
        player_id="player-1",
    )

    jobs = repo.list_jobs(federation_id="fed_alpha")
    sessions = repo.list_sessions(federation_id="fed_alpha")

    assert len(jobs) == 1
    assert jobs[0]["federation_id"] == "fed_alpha"
    assert len(sessions) == 1
    assert sessions[0]["federation_id"] == "fed_alpha"
    assert repo.list_jobs(federation_id="fed_beta") == []
    assert repo.list_sessions(federation_id="fed_beta") == []
