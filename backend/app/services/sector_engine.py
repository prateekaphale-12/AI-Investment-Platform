"""
Sector enforcement and constraint engine.

Ensures portfolio respects user-selected sectors and explains exclusions.

Features:
- Enforce sector constraints
- Minimum sector representation
- Explain why sectors were excluded
- Rebalance allocations to meet sector targets
- Track sector exposure
"""

from __future__ import annotations

from typing import Any
from loguru import logger

# Sector to tickers mapping (must match stock_universe.py)
SECTOR_TICKERS: dict[str, list[str]] = {
    "technology": ["AAPL", "MSFT", "GOOGL", "META", "CRM", "ORCL"],
    "semiconductors": ["NVDA", "AMD", "INTC", "AVGO", "QCOM", "MU"],
    "healthcare": ["JNJ", "UNH", "LLY", "PFE", "ABBV"],
    "financials": ["JPM", "BAC", "GS", "MS", "V"],
    "consumer": ["AMZN", "TSLA", "HD", "NKE", "MCD"],
    "energy": ["XOM", "CVX", "COP"],
}


def _get_ticker_sector(ticker: str) -> str | None:
    """Get sector for a ticker"""
    for sector, tickers in SECTOR_TICKERS.items():
        if ticker in tickers:
            return sector
    return None


def _get_sector_exposure(allocations: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate sector exposure from allocations
    
    Returns dict of sector -> total allocation %
    """
    exposure: dict[str, float] = {}
    
    for alloc in allocations:
        ticker = alloc.get("ticker")
        sector = _get_ticker_sector(ticker)
        if sector:
            exposure[sector] = exposure.get(sector, 0.0) + alloc.get("allocation_pct", 0.0)
    
    return exposure


def _get_missing_sectors(
    selected_sectors: list[str],
    allocations: list[dict[str, Any]],
) -> list[str]:
    """Get sectors selected by user but not represented in portfolio
    
    Returns list of missing sector names
    """
    exposure = _get_sector_exposure(allocations)
    missing = []
    
    for sector in selected_sectors:
        if sector not in exposure or exposure[sector] < 0.1:  # Less than 0.1% = missing
            missing.append(sector)
    
    return missing


def validate_sector_constraints(
    selected_sectors: list[str],
    allocations: list[dict[str, Any]],
    min_sector_pct: float = 10.0,
) -> dict[str, Any]:
    """
    Validate that portfolio respects sector constraints.
    
    Returns:
    {
        "valid": bool,
        "exposure": {sector: %},
        "missing_sectors": [sector],
        "under_represented": {sector: current%},
        "warnings": [str],
        "recommendations": [str],
    }
    """
    exposure = _get_sector_exposure(allocations)
    missing = _get_missing_sectors(selected_sectors, allocations)
    under_represented = {}
    warnings = []
    recommendations = []
    
    # Check for under-represented sectors
    for sector in selected_sectors:
        current = exposure.get(sector, 0.0)
        if current < min_sector_pct and current > 0.1:
            under_represented[sector] = current
            warnings.append(
                f"{sector.capitalize()} exposure {current:.1f}% is below target {min_sector_pct}%"
            )
    
    # Check for missing sectors
    if missing:
        warnings.append(
            f"Missing sectors: {', '.join(s.capitalize() for s in missing)}"
        )
        for sector in missing:
            recommendations.append(
                f"Consider adding {sector} exposure (currently 0%)"
            )
    
    # Check for over-concentration
    for sector, pct in exposure.items():
        if pct > 40:
            warnings.append(
                f"{sector.capitalize()} is over-concentrated at {pct:.1f}%"
            )
            recommendations.append(
                f"Consider reducing {sector} exposure to <40%"
            )
    
    valid = len(missing) == 0 and len(under_represented) == 0
    
    return {
        "valid": valid,
        "exposure": exposure,
        "missing_sectors": missing,
        "under_represented": under_represented,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def explain_sector_exclusions(
    selected_sectors: list[str],
    allocations: list[dict[str, Any]],
    tickers_data: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Explain why sectors were excluded from portfolio.
    
    Returns:
    {
        "excluded_sectors": [sector],
        "exclusion_reasons": {sector: reason},
        "available_tickers": {sector: [tickers]},
        "quality_scores": {sector: score},
    }
    """
    exposure = _get_sector_exposure(allocations)
    excluded = [s for s in selected_sectors if s not in exposure or exposure[s] < 0.1]
    
    exclusion_reasons = {}
    available_tickers = {}
    quality_scores = {}
    
    # Get tickers in portfolio
    portfolio_tickers = {a.get("ticker") for a in allocations}
    
    for sector in excluded:
        sector_tickers = SECTOR_TICKERS.get(sector, [])
        available_tickers[sector] = sector_tickers
        
        # Find why this sector was excluded
        sector_data = [t for t in tickers_data if t.get("ticker") in sector_tickers]
        
        if not sector_data:
            exclusion_reasons[sector] = f"No {sector} stocks in analysis universe"
            quality_scores[sector] = 0.0
        else:
            # Calculate average confidence for sector
            avg_confidence = sum(
                t.get("confidence", {}).get("final_confidence", 0.5)
                for t in sector_data
            ) / len(sector_data)
            
            quality_scores[sector] = avg_confidence
            
            if avg_confidence < 0.45:
                exclusion_reasons[sector] = (
                    f"{sector.capitalize()} stocks show weak conviction "
                    f"(avg confidence {avg_confidence:.0%}). "
                    f"Deprioritized in favor of higher-conviction opportunities."
                )
            elif avg_confidence < 0.55:
                exclusion_reasons[sector] = (
                    f"{sector.capitalize()} stocks show moderate conviction "
                    f"(avg confidence {avg_confidence:.0%}). "
                    f"Limited allocation due to stronger alternatives."
                )
            else:
                exclusion_reasons[sector] = (
                    f"{sector.capitalize()} stocks available but not selected "
                    f"due to portfolio construction constraints."
                )
    
    return {
        "excluded_sectors": excluded,
        "exclusion_reasons": exclusion_reasons,
        "available_tickers": available_tickers,
        "quality_scores": quality_scores,
    }


def rebalance_for_sector_targets(
    allocations: list[dict[str, Any]],
    selected_sectors: list[str],
    min_sector_pct: float = 10.0,
    max_iterations: int = 10,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Rebalance allocations to meet sector targets.
    
    This is a soft constraint - tries to meet targets but maintains
    confidence-driven weighting as much as possible.
    
    Returns:
    (rebalanced_allocations, rebalance_info)
    """
    if not allocations or not selected_sectors:
        return allocations, {"rebalanced": False, "reason": "No allocations or sectors"}
    
    current_exposure = _get_sector_exposure(allocations)
    missing = _get_missing_sectors(selected_sectors, allocations)
    
    if not missing:
        return allocations, {"rebalanced": False, "reason": "All sectors represented"}
    
    # For now, return original allocations with explanation
    # Full rebalancing would require more complex optimization
    
    return allocations, {
        "rebalanced": False,
        "reason": f"Missing sectors: {', '.join(missing)}. "
                  f"Consider running analysis with different parameters.",
        "missing_sectors": missing,
        "current_exposure": current_exposure,
    }


def build_sector_report(
    selected_sectors: list[str],
    allocations: list[dict[str, Any]],
    tickers_data: list[dict[str, Any]],
) -> str:
    """
    Build human-readable sector report.
    
    Returns markdown-formatted report explaining sector allocation.
    """
    validation = validate_sector_constraints(selected_sectors, allocations)
    exclusions = explain_sector_exclusions(selected_sectors, allocations, tickers_data)
    
    lines = []
    lines.append("## Sector Analysis\n")
    
    # Current exposure
    lines.append("### Current Sector Exposure\n")
    exposure = validation["exposure"]
    if exposure:
        for sector in sorted(exposure.keys()):
            pct = exposure[sector]
            lines.append(f"- **{sector.capitalize()}**: {pct:.1f}%")
    else:
        lines.append("- No sector exposure data available")
    lines.append("")
    
    # Warnings
    if validation["warnings"]:
        lines.append("### Warnings\n")
        for warning in validation["warnings"]:
            lines.append(f"- ⚠️ {warning}")
        lines.append("")
    
    # Recommendations
    if validation["recommendations"]:
        lines.append("### Recommendations\n")
        for rec in validation["recommendations"]:
            lines.append(f"- 💡 {rec}")
        lines.append("")
    
    # Exclusions
    if exclusions["excluded_sectors"]:
        lines.append("### Excluded Sectors\n")
        for sector in exclusions["excluded_sectors"]:
            reason = exclusions["exclusion_reasons"].get(sector, "Unknown reason")
            quality = exclusions["quality_scores"].get(sector, 0.0)
            lines.append(f"- **{sector.capitalize()}** (quality: {quality:.0%})")
            lines.append(f"  - {reason}")
        lines.append("")
    
    # Validation status
    if validation["valid"]:
        lines.append("✅ **Portfolio respects all sector constraints**\n")
    else:
        lines.append("⚠️ **Portfolio does not fully meet sector constraints**\n")
    
    return "\n".join(lines)


def get_sector_statistics(
    allocations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Get sector statistics from allocations.
    
    Returns:
    {
        "sector_count": int,
        "exposure": {sector: %},
        "concentration": float (0-1, 0=diversified, 1=concentrated),
        "largest_sector": (sector, %),
        "smallest_sector": (sector, %),
    }
    """
    exposure = _get_sector_exposure(allocations)
    
    if not exposure:
        return {
            "sector_count": 0,
            "exposure": {},
            "concentration": 0.0,
            "largest_sector": None,
            "smallest_sector": None,
        }
    
    # Calculate Herfindahl index (concentration measure)
    herfindahl = sum(pct ** 2 for pct in exposure.values()) / 10000
    
    largest = max(exposure.items(), key=lambda x: x[1]) if exposure else None
    smallest = min(exposure.items(), key=lambda x: x[1]) if exposure else None
    
    return {
        "sector_count": len(exposure),
        "exposure": exposure,
        "concentration": herfindahl,
        "largest_sector": largest,
        "smallest_sector": smallest,
    }
