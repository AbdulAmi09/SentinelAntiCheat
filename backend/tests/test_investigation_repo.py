from __future__ import annotations

from pathlib import Path

from sentinel.repositories.investigation import InvestigationRepository


def test_case_reviews_and_signoffs_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "investigation.db"
    repo = InvestigationRepository(str(db))
    case = repo.create_case(
        title="Test Case",
        status="opened",
        players=["p1"],
        event_id="evt-1",
        summary=None,
        tags=[],
        priority=None,
        assigned_to=None,
    )

    review = repo.add_review(
        case["id"],
        reviewer_user_id="arbiter-1",
        action="recommend_escalation",
        rationale="Escalate for chief review",
        payload={"source": "dashboard"},
    )
    signoff = repo.add_signoff(
        case["id"],
        signer_user_id="chief-1",
        signer_role="chief_arbiter",
        decision="approved",
        note="Approved for action",
    )

    reviews = repo.list_reviews(case["id"])
    signoffs = repo.list_signoffs(case["id"])

    assert reviews[0]["id"] == review["id"]
    assert reviews[0]["action"] == "recommend_escalation"
    assert signoffs[0]["id"] == signoff["id"]
    assert signoffs[0]["decision"] == "approved"
