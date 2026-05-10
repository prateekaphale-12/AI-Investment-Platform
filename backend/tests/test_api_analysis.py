from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_analysis_endpoints_happy_path(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "test_app.db"
    monkeypatch.setattr(settings, "database_path", db_path)

    async def _fake_execute_analysis(session_id: str) -> None:
        from app.db.init_db import get_connection
        from app.services import analysis_db as adb

        db = await get_connection()
        try:
            await adb.set_agent_status(db, session_id, "planner", "completed")
            await adb.set_agent_status(db, session_id, "market_research", "completed")
            await adb.set_agent_status(db, session_id, "financial_analysis", "completed")
            await adb.set_agent_status(db, session_id, "technical_analysis", "completed")
            await adb.set_agent_status(db, session_id, "news_sentiment", "completed")
            await adb.set_agent_status(db, session_id, "risk_analysis", "completed")
            await adb.set_agent_status(db, session_id, "portfolio_allocation", "completed")
            await adb.set_agent_status(db, session_id, "report_generation", "completed")
            await adb.finalize_session(
                db,
                session_id,
                status="completed",
                summary={
                    "total_budget": 50000,
                    "total_expected_return": 8.2,
                    "overall_risk": "medium",
                    "diversification_score": 74.0,
                    "best_performer": "NVDA",
                    "recommended_action": "Research & due diligence only — not investment advice.",
                },
                market_data={"NVDA": {"ticker": "NVDA", "current_price": 900.0}},
                technical_data={"NVDA": {"signal": "bullish", "rsi": 58.1}},
                portfolio={
                    "allocations": [
                        {
                            "ticker": "NVDA",
                            "allocation_pct": 100.0,
                            "amount": 50000.0,
                            "expected_return": 8.2,
                            "risk_score": 45.0,
                            "rationale": {"market_trend": "Uptrend", "technical": "Bullish", "summary": "Strong setup"},
                        }
                    ]
                },
                report="# Test Report",
                report_id=f"r-{session_id[:8]}",
            )
        finally:
            await db.close()

    import app.api.v1.endpoints.analysis as analysis_endpoint

    monkeypatch.setattr(analysis_endpoint, "execute_analysis", _fake_execute_analysis)

    with TestClient(app) as client:
        payload = {
            "budget": 50000,
            "risk_tolerance": "medium",
            "investment_horizon": "1y",
            "interests": ["Technology"],
            "goal": "growth",
        }
        create = client.post("/api/v1/analyze", json=payload)
        assert create.status_code == 202
        session_id = create.json()["session_id"]

        status = client.get(f"/api/v1/analysis/{session_id}/status")
        assert status.status_code == 200
        assert status.json()["status"] == "completed"

        results = client.get(f"/api/v1/analysis/{session_id}/results")
        assert results.status_code == 200
        body = results.json()
        assert body["status"] == "completed"
        assert body["summary"]["total_budget"] == 50000
        assert body["portfolio"]["allocations"][0]["ticker"] == "NVDA"


def test_analysis_status_not_found(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_path", tmp_path / "test_app.db")
    with TestClient(app) as client:
        res = client.get("/api/v1/analysis/does-not-exist/status")
        assert res.status_code == 404
