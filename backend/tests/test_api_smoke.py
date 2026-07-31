from fastapi.testclient import TestClient

# Client fixture is now provided by conftest.py


def _auth_headers(client: TestClient) -> dict[str, str]:
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "Pass12345!"},
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_and_capabilities_endpoints(client: TestClient) -> None:
    h = client.get("/api/v1/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"

    c = client.get("/api/v1/capabilities")
    assert c.status_code == 200
    body = c.json()

    assert "groq_configured" in body
    assert "groq_model" in body

    assert "openai_configured" in body
    assert "openai_model" in body


def test_analyze_accepts_request_and_creates_session(client: TestClient, monkeypatch) -> None:

    # Avoid network-heavy background execution in smoke tests.
    from app.api.v1.endpoints import analysis as analysis_ep

    async def _noop_execute_analysis(_: str) -> None:
        return None

    monkeypatch.setattr(analysis_ep, "execute_analysis", _noop_execute_analysis)

    headers = _auth_headers(client)
    payload = {
        "budget": 50000,
        "risk_tolerance": "medium",
        "investment_horizon": "1y",
        "interests": ["Technology"],
        "goal": "growth",
    }
    res = client.post("/api/v1/analyze", json=payload, headers=headers)
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "processing"
    session_id = body["session_id"]
    assert session_id

    status = client.get(f"/api/v1/analysis/{session_id}/status", headers=headers)
    assert status.status_code == 200
    s_body = status.json()
    assert s_body["session_id"] == session_id
    assert s_body["status"] in {"processing", "completed", "failed"}
