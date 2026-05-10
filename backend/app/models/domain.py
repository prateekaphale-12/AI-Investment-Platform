from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    budget: float = Field(gt=0, description="Investment budget in base currency")
    risk_tolerance: Literal["low", "medium", "high"]
    investment_horizon: str = Field(
        default="1y",
        description="e.g. 3m, 6m, 1y, 3y",
    )
    interests: list[str] = Field(
        default_factory=list,
        description="Sectors or themes, e.g. Technology, Semiconductors",
    )
    goal: Literal["growth", "income", "balanced"] = "balanced"


class TickerRationale(BaseModel):
    market_trend: str = ""
    technical: str = ""
    sentiment: str = ""
    fundamentals: str = ""
    risk: str = ""
    summary: str = ""


class AllocationItem(BaseModel):
    ticker: str
    allocation_pct: float
    amount: float
    expected_return: float = Field(
        ...,
        description="Heuristic momentum proxy, not a forecast",
    )
    risk_score: float = Field(..., ge=0, le=100)
    rationale: TickerRationale


class AnalysisSummary(BaseModel):
    total_budget: float
    total_expected_return: float
    overall_risk: Literal["low", "medium", "high"]
    diversification_score: float = Field(ge=0, le=100)
    best_performer: str | None = None
    recommended_action: str = Field(
        default="Research & due diligence only — not investment advice.",
    )


class AnalysisResultsResponse(BaseModel):
    session_id: str
    status: Literal["processing", "completed", "failed"]
    summary: AnalysisSummary | None = None
    market_data: dict[str, dict[str, Any]] = Field(default_factory=dict)
    technical_data: dict[str, dict[str, Any]] = Field(default_factory=dict)
    portfolio: dict[str, Any] = Field(default_factory=dict)
    report: str = ""
    report_id: str = ""
    errors: list[str] = Field(default_factory=list)


class AnalysisStatusResponse(BaseModel):
    session_id: str
    status: Literal["processing", "completed", "failed"]
    current_agent: str | None = None
    agents_completed: int = 0
    agents_total: int = 4
    errors: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


class WatchlistAddRequest(BaseModel):
    session_id: str | None = None
    ticker: str
    ticker_name: str | None = None


class WatchlistItem(BaseModel):
    id: str
    session_id: str | None
    ticker: str
    ticker_name: str | None
    added_at: str


class WatchlistItemsResponse(BaseModel):
    items: list[WatchlistItem]
