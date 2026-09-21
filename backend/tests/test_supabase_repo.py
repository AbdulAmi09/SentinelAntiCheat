from __future__ import annotations

import ssl
from urllib import error

from sentinel.repositories.supabase import SupabaseConfig, SupabaseRepository


def test_supabase_post_retries_on_ssl_bad_record_mac(monkeypatch) -> None:
    repo = SupabaseRepository(SupabaseConfig(url="https://example.supabase.co", service_role_key="k"))
    attempts = {"n": 0}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def _fake_urlopen(req, timeout, context):  # noqa: ANN001
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise ssl.SSLError("[SSL: SSLV3_ALERT_BAD_RECORD_MAC] sslv3 alert bad record mac (_ssl.c:2546)")
        return _Resp()

    monkeypatch.setattr("sentinel.repositories.supabase.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("sentinel.repositories.supabase.time.sleep", lambda *_: None)

    repo._post("players", [{"id": "p1"}], prefer="return=minimal")
    assert attempts["n"] == 3


def test_supabase_post_does_not_retry_on_client_http_error(monkeypatch) -> None:
    repo = SupabaseRepository(SupabaseConfig(url="https://example.supabase.co", service_role_key="k"))
    attempts = {"n": 0}

    def _fake_urlopen(req, timeout, context):  # noqa: ANN001
        attempts["n"] += 1
        raise error.HTTPError(url=str(req.full_url), code=400, msg="bad request", hdrs=None, fp=None)

    monkeypatch.setattr("sentinel.repositories.supabase.request.urlopen", _fake_urlopen)
    monkeypatch.setattr("sentinel.repositories.supabase.time.sleep", lambda *_: None)

    raised = False
    try:
        repo._post("players", [{"id": "p1"}], prefer="return=minimal")
    except error.HTTPError:
        raised = True
    assert raised is True
    assert attempts["n"] == 1


def test_resolve_federation_id_prefers_explicit_header() -> None:
    assert SupabaseRepository._resolve_federation_id("fedA::event-12", "fedB") == "fedB"
    assert SupabaseRepository._resolve_federation_id("fedA::event-12", None) == "fedA"
    assert SupabaseRepository._resolve_federation_id("event-12", None) is None


def test_persist_analysis_populates_federation_and_report_version(monkeypatch) -> None:
    repo = SupabaseRepository(SupabaseConfig(url="https://example.supabase.co", service_role_key="k"))
    calls: list[tuple[str, list[dict], str | None]] = []

    def _capture(path, payload, prefer=None):  # noqa: ANN001
        calls.append((path, payload, prefer))

    monkeypatch.setattr(repo, "_post", _capture)

    response_payload = {
        "risk_tier": "HIGH_STATISTICAL_ANOMALY",
        "confidence": 0.91,
        "analyzed_move_count": 42,
        "triggered_signals": 4,
        "explanation": ["Weighted fusion override"],
        "signals": [{"name": "Layer1_IPR_MoveQuality", "triggered": True, "score": 5.3, "threshold": 4.25, "reasons": ["Regan threshold exceeded"]}],
        "report_version": 2,
        "report_locked": True,
        "report_locked_at": "2026-03-09T10:00:00+00:00",
        "explainability_method": "shap_proxy_v1",
        "explainability_items": [{"feature": "regan_z_score", "contribution": 0.7, "direction": "increases_risk"}],
        "ml_fusion_source": "heuristic_xgb_iforest",
        "ml_primary_score": 0.78,
        "ml_secondary_score": 0.61,
<<<<<<< HEAD
        "chain_hash": "chain-1",
        "prev_chain_hash": "chain-0",
        "evidence_report": {"summary": "compressed"},
        "behavioral_metrics": {"move_time_consistency": 0.81},
        "environmental_metrics": {"focus_windows": 2},
        "identity_confidence": {"device": 0.73},
        "confidence_intervals": {"weighted_risk_score": [0.82, 0.91]},
        "ipr_estimate": 5.2,
        "pep_score": 0.14,
        "regan_z_score": 4.6,
        "report_workflow": {"locked_by": "chief_arbiter"},
=======
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    }

    repo.persist_analysis(
        player_id="player-1",
        event_id="fedA::event-12",
        federation_id=None,
        event_type="online",
        audit_id="audit-123",
        weighted_risk_score=0.88,
        regan_threshold_used=4.25,
        natural_occurrence_statement="The observed performance has an estimated probability of natural occurrence of approximately 1 in 20,000 games among players of similar rating and history.",
        natural_occurrence_probability=0.00005,
        model_version="v0.2",
        feature_schema_version="v1",
        report_schema_version="v1",
        legal_disclaimer_text="Statistical anomaly assessment only.",
        human_review_required=True,
        response_payload=response_payload,
        request_payload={"player_id": "player-1"},
    )

    assert any(path.startswith("federations") for path, _, _ in calls)
    event_call = next(payload for path, payload, _ in calls if path.startswith("events"))
<<<<<<< HEAD
    analysis_call = next(payload for path, payload, _ in calls if path.startswith("analyses"))
=======
    analysis_call = next(payload for path, payload, _ in calls if path == "analyses")
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
    report_call = next(payload for path, payload, _ in calls if path.startswith("report_versions"))

    assert event_call[0]["federation_id"] == "fedA"
    assert analysis_call[0]["federation_id"] == "fedA"
    assert analysis_call[0]["review_status"] == "under_review"
    assert analysis_call[0]["explainability_method"] == "shap_proxy_v1"
<<<<<<< HEAD
    assert analysis_call[0]["chain_hash"] == "chain-1"
    assert analysis_call[0]["report_workflow"] == {"locked_by": "chief_arbiter"}
    assert report_call[0]["analysis_external_audit_id"] == "audit-123"
    assert report_call[0]["version_no"] == 2


def test_persist_partner_job_uses_idempotent_upserts(monkeypatch) -> None:
    repo = SupabaseRepository(SupabaseConfig(url="https://example.supabase.co", service_role_key="k"))
    calls: list[tuple[str, list[dict], str | None]] = []

    def _capture(path, payload, prefer=None):  # noqa: ANN001
        calls.append((path, payload, prefer))

    monkeypatch.setattr(repo, "_post", _capture)

    repo.persist_partner_job(
        job_id="job-123",
        api_key_id="key-1",
        federation_id="fed-alpha",
        game_id="game-9",
        player_id="player-3",
        raw_payload={"pgn": "1. e4 e5"},
        status="queued",
        webhook_url="https://example.com/hook",
    )

    assert calls[0][0] == "partner_jobs?on_conflict=job_id"
    assert calls[0][2] == "resolution=merge-duplicates,return=minimal"
    assert calls[0][1][0]["federation_id"] == "fed-alpha"
    assert calls[1][0] == "partner_payloads?on_conflict=job_id"
    assert calls[1][2] == "resolution=merge-duplicates,return=minimal"
=======
    assert report_call[0]["analysis_external_audit_id"] == "audit-123"
    assert report_call[0]["version_no"] == 2
>>>>>>> f27ff144a8ecc8ace559ec86547e0cd2d9dd3674
