from __future__ import annotations

from typing import Any, Literal

from app.services.allocation_engine import build_allocations_confidence_driven
from app.services.probabilistic_optimizer import ProbabilisticOptimizer
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
    use_probabilistic: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Build portfolio allocations using confidence-driven weighting or probabilistic optimization.
    
    tickers_data items: ticker, market row, technical row, sentiment row, confidence, rationale.
    
    Args:
        budget: Total portfolio budget
        risk_tolerance: "low", "medium", or "high"
        tickers_data: List of stock data
        selected_sectors: Optional sector constraints
        use_probabilistic: If True, use probabilistic optimizer; else use confidence-driven
    
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

    # Choose allocation method
    if use_probabilistic and len(tickers_data) >= 3:
        # Use probabilistic optimizer for more sophisticated analysis
        try:
            optimizer = ProbabilisticOptimizer()
            constraints = {
                "min_position_pct": 2.0,
                "max_position_pct": 30.0,
            }
            allocations, portfolio_metrics = optimizer.optimize(
                budget,
                risk_tolerance,
                tickers_data,
                constraints=constraints,
            )
            
            # Build summary from portfolio metrics
            summary = {
                "total_budget": budget,
                "total_expected_return": portfolio_metrics.get("expected_return", 0.0),
                "overall_risk": risk_tolerance,
                "diversification_score": portfolio_metrics.get("diversification_score", 0.0),
                "best_performer": max(
                    tickers_data,
                    key=lambda r: float((r.get("market", {}).get("ytd_return_pct") or 0.0))
                ).get("ticker"),
                "recommended_action": "Research & due diligence only — not investment advice.",
                "portfolio_metrics": portfolio_metrics,
                "optimization_method": "probabilistic",
            }
        except Exception as e:
            # Fallback to confidence-driven if probabilistic fails
            from loguru import logger
            logger.warning(f"Probabilistic optimization failed, falling back to confidence-driven: {e}")
            allocations, summary = build_allocations_confidence_driven(
                budget,
                risk_tolerance,
                tickers_data,
            )
            summary["optimization_method"] = "confidence_driven_fallback"
    else:
        # Use confidence-driven allocation engine
        allocations, summary = build_allocations_confidence_driven(
            budget,
            risk_tolerance,
            tickers_data,
        )
        summary["optimization_method"] = "confidence_driven"
    
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
