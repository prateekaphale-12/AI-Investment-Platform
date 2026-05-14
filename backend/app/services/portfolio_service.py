from __future__ import annotations

from typing import Any, Literal

from app.services.allocation_engine import build_allocations_confidence_driven
from app.services.sector_engine import (
    build_sector_report,
    explain_sector_exclusions,
    validate_sector_constraints,
)

Risk = Literal["low", "medium", "high"]


def build_allocations(
    budget: float,
    risk_tolerance: Risk,
    tickers_data: list[dict[str, Any]],
    selected_sectors: list[str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Build portfolio allocations using confidence-driven weighting.
    
    tickers_data items: ticker, market row, technical row, sentiment row, confidence, rationale.
    
    Returns:
        (allocations_list, summary_dict)
    """
    if not tickers_data:
        return [], {
            "total_budget": budget,
            "total_expected_return": 0.0,
            "overall_risk": risk_tolerance,
            "diversification_score": 0.0,
            "best_performer": None,
            "recommended_action": "Insufficient data for allocation.",
            "sector_analysis": None,
        }

    # Use confidence-driven allocation engine
    allocations, summary = build_allocations_confidence_driven(
        budget,
        risk_tolerance,
        tickers_data,
    )
    
    # Add sector analysis if sectors were selected
    if selected_sectors:
        sector_validation = validate_sector_constraints(selected_sectors, allocations)
        sector_exclusions = explain_sector_exclusions(selected_sectors, allocations, tickers_data)
        sector_report = build_sector_report(selected_sectors, allocations, tickers_data)
        
        summary["sector_analysis"] = {
            "selected_sectors": selected_sectors,
            "validation": sector_validation,
            "exclusions": sector_exclusions,
            "report": sector_report,
        }
    
    return allocations, summary
