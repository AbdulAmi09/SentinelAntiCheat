from fastapi.testclient import TestClient

from sentinel.main import app


def test_system_status_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/v1/system-status")
    assert resp.status_code == 200
    payload = resp.json()

    for key in [
        "generated_at_utc",
        "calibration",
        "ml_fusion",
        "maia",
        "engine",
        "lc0_ready",
        "maia_models_detected",
        "ml_models_loaded",
        "analysis_pipeline_operational",
        "warnings",
    ]:
        assert key in payload
