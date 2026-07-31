"""
Intelligent Stock Screener - Deep AI-driven stock selection

This module implements a two-stage screening process:
1. Broad screening: Filter candidates based on basic criteria
2. Deep analysis: AI evaluates each candidate against user profile

For short-term horizons, this is CRITICAL - we need momentum, catalysts, and timing.
"""

from __future__ import annotations

from typing import Any
import asyncio
import yfinance as yf
from loguru import logger


async def intelligent_stock_screening(
    user_profile: dict[str, Any],
    candidate_tickers: list[str],
    llm_generate_func: Any,
) -> dict[str, Any]:
    """
    Perform intelligent two-stage stock screening.
    
    Args:
        user_profile: User's investment profile (risk, goal, horizon, budget, sectors)
        candidate_tickers: List of candidate tickers to screen
        llm_generate_func: Function to call LLM for analysis
    
    Returns:
        {
            "selected_stocks": [list of tickers],
            "screening_report": {
                "stage1_candidates": int,
                "stage2_analyzed": int,
                "final_selected": int,
                "screening_criteria": str,
            },
            "stock_analysis": {
                "TICKER": {
                    "score": float,
                    "reasoning": str,
                    "key_factors": [str],
                    "risks": [str],
                    "catalysts": [str],
                }
            }
        }
    """
    risk = user_profile.get("risk_tolerance", "medium")
    goal = user_profile.get("goal", "growth")
    horizon = user_profile.get("investment_horizon", "1 year")
    budget = user_profile.get("budget", 10000)
    sectors = user_profile.get("sectors", [])
    
    # Stage 1: Broad screening (quick filters)
    stage1_candidates = await _stage1_broad_screening(
        candidate_tickers,
        risk,
        goal,
        horizon
    )
    
    logger.info(f"Stage 1: {len(candidate_tickers)} candidates → {len(stage1_candidates)} passed broad screening")
    
    # Stage 2: Deep AI analysis
    stock_analysis = await _stage2_deep_analysis(
        stage1_candidates,
        user_profile,
        llm_generate_func
    )
    
    # Stage 3: Final selection based on scores
    selected_stocks = _stage3_final_selection(
        stock_analysis,
        risk,
        goal,
        horizon
    )
    
    logger.info(f"Stage 2: {len(stage1_candidates)} analyzed → {len(selected_stocks)} selected")
    
    return {
        "selected_stocks": selected_stocks,
        "screening_report": {
            "stage1_candidates": len(candidate_tickers),
            "stage2_analyzed": len(stage1_candidates),
            "final_selected": len(selected_stocks),
            "screening_criteria": _build_screening_criteria_summary(risk, goal, horizon),
        },
        "stock_analysis": stock_analysis,
    }


async def _stage1_broad_screening(
    tickers: list[str],
    risk: str,
    goal: str,
    horizon: str
) -> list[str]:
    """
    Stage 1: Broad screening with basic filters.
    
    Filters:
    - Market cap (avoid micro-caps for low risk)
    - Liquidity (average volume > 1M shares/day)
    - Price (avoid penny stocks < $5)
    - Data availability (must have recent data)
    """
    
    async def check_ticker(ticker: str) -> tuple[str, bool]:
        try:
            t = yf.Ticker(ticker)
            info = await asyncio.to_thread(lambda: t.info)
            
            # Filter 1: Market cap
            market_cap = info.get("marketCap", 0)
            if risk == "low" and market_cap < 10e9:  # < $10B for low risk
                return (ticker, False)
            if market_cap < 1e9:  # < $1B (too small)
                return (ticker, False)
            
            # Filter 2: Liquidity
            avg_volume = info.get("averageVolume", 0)
            if avg_volume < 1e6:  # < 1M shares/day
                return (ticker, False)
            
            # Filter 3: Price
            current_price = info.get("currentPrice", 0)
            if current_price < 5:  # Penny stock
                return (ticker, False)
            
            # Filter 4: Data availability
            if not info.get("trailingPE") and not info.get("forwardPE"):
                return (ticker, False)  # No valuation data
            
            return (ticker, True)
        except Exception as e:
            logger.warning(f"Stage 1 screening failed for {ticker}: {e}")
            return (ticker, False)
    
    # Check all tickers in parallel
    results = await asyncio.gather(*[check_ticker(t) for t in tickers])
    passed = [ticker for ticker, passed in results if passed]
    
    return passed


async def _stage2_deep_analysis(
    tickers: list[str],
    user_profile: dict[str, Any],
    llm_generate_func: Any
) -> dict[str, dict]:
    """
    Stage 2: Deep AI analysis of each candidate.
    
    For each stock, AI evaluates:
    - Alignment with user profile (risk, goal, horizon)
    - Current momentum and catalysts
    - Risk factors and concerns
    - Scoring (0-100)
    """
    risk = user_profile.get("risk_tolerance", "medium")
    goal = user_profile.get("goal", "growth")
    horizon = user_profile.get("investment_horizon", "1 year")
    
    # Get quick fundamental data for all candidates in parallel
    async def get_stock_data(ticker: str) -> tuple[str, dict]:
        try:
            t = yf.Ticker(ticker)
            info = await asyncio.to_thread(lambda: t.info)
            return (ticker, {
                "name": info.get("shortName", ticker),
                "sector": info.get("sector", "Unknown"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "profit_margin": info.get("profitMargins"),
                "beta": info.get("beta"),
                "52w_change": info.get("52WeekChange"),
                "analyst_target": info.get("targetMeanPrice"),
                "current_price": info.get("currentPrice"),
            })
        except Exception as e:
            logger.warning(f"Failed to get data for {ticker}: {e}")
            return (ticker, None)
    
    results = await asyncio.gather(*[get_stock_data(t) for t in tickers])
    stock_data = {ticker: data for ticker, data in results if data is not None}
    
    if not stock_data:
        logger.error("No stock data available for deep analysis")
        return {}
    
    # Build comprehensive analysis prompt
    analysis_prompt = f"""You are an expert investment analyst performing DEEP stock screening.

USER PROFILE:
- Risk Tolerance: {risk}
- Investment Goal: {goal}
- Time Horizon: {horizon}
- Budget: ${user_profile.get('budget', 10000):,}

SCREENING TASK:
Analyze each stock below and score it (0-100) based on how well it matches the user profile.

CRITICAL FACTORS FOR {horizon.upper()} HORIZON:
"""

    # Add horizon-specific criteria
    if "month" in horizon.lower() or "short" in horizon.lower() or "<" in horizon.lower():
        analysis_prompt += """
SHORT-TERM FOCUS (Critical for <1 year):
1. **Momentum**: Recent price action, technical strength, volume trends
2. **Catalysts**: Upcoming earnings, product launches, regulatory decisions
3. **Volatility**: Can user handle swings? Match to risk tolerance
4. **Sentiment**: News flow, analyst upgrades, insider buying
5. **Timing**: Is NOW the right entry point? Or wait?
"""
    elif "year" in horizon.lower() and not "5" in horizon and not "10" in horizon:
        analysis_prompt += """
MEDIUM-TERM FOCUS (1-3 years):
1. **Growth Trajectory**: Revenue/earnings growth sustainability
2. **Competitive Position**: Moat, market share, pricing power
3. **Catalysts**: Multi-quarter themes (AI, GLP-1, cloud, etc.)
4. **Valuation**: PEG ratio, growth vs price
5. **Risk/Reward**: Upside potential vs downside protection
"""
    else:
        analysis_prompt += """
LONG-TERM FOCUS (3+ years):
1. **Secular Trends**: Long-term tailwinds (AI, aging, digitization)
2. **Compounding**: ROE, ROIC, reinvestment opportunities
3. **Management**: Capital allocation, execution track record
4. **Moat**: Sustainable competitive advantages
5. **Valuation**: Margin of safety for long-term hold
"""

    analysis_prompt += f"""

GOAL ALIGNMENT ({goal.upper()}):
"""
    if goal == "growth":
        analysis_prompt += "- Prioritize revenue/earnings growth, expanding margins, market share gains\n"
        analysis_prompt += "- Accept higher volatility for higher returns\n"
        analysis_prompt += "- Look for secular trends and catalysts\n"
    elif goal == "income":
        analysis_prompt += "- Prioritize dividend yield, payout sustainability, cash flow stability\n"
        analysis_prompt += "- Prefer lower volatility, defensive sectors\n"
        analysis_prompt += "- Look for dividend growth track record\n"
    else:  # balanced
        analysis_prompt += "- Balance growth and income, stability and upside\n"
        analysis_prompt += "- Moderate volatility acceptable\n"
        analysis_prompt += "- Look for quality compounders\n"

    analysis_prompt += f"""

RISK ALIGNMENT ({risk.upper()} RISK):
"""
    if risk == "low":
        analysis_prompt += "- Prefer large-cap, low beta, stable businesses\n"
        analysis_prompt += "- Avoid high volatility, speculative plays\n"
        analysis_prompt += "- Prioritize downside protection over upside\n"
    elif risk == "high":
        analysis_prompt += "- Accept high volatility for high returns\n"
        analysis_prompt += "- Consider smaller caps, growth stories\n"
        analysis_prompt += "- Prioritize upside potential\n"
    else:  # medium
        analysis_prompt += "- Balance stability and growth\n"
        analysis_prompt += "- Moderate volatility acceptable\n"
        analysis_prompt += "- Mix of large-cap stability and growth opportunities\n"

    analysis_prompt += """

STOCKS TO ANALYZE:
"""
    
    for ticker, data in stock_data.items():
        mc_str = f"${data['market_cap']/1e9:.1f}B" if data['market_cap'] else "N/A"
        pe_str = f"{data['pe_ratio']:.1f}" if data['pe_ratio'] else "N/A"
        peg_str = f"{data['peg_ratio']:.2f}" if data['peg_ratio'] else "N/A"
        rg_str = f"{data['revenue_growth']*100:.1f}%" if data['revenue_growth'] else "N/A"
        eg_str = f"{data['earnings_growth']*100:.1f}%" if data['earnings_growth'] else "N/A"
        pm_str = f"{data['profit_margin']*100:.1f}%" if data['profit_margin'] else "N/A"
        beta_str = f"{data['beta']:.2f}" if data['beta'] else "N/A"
        chg_str = f"{data['52w_change']*100:.1f}%" if data['52w_change'] else "N/A"
        target_str = f"${data['analyst_target']:.2f}" if data['analyst_target'] else "N/A"
        price_str = f"${data['current_price']:.2f}" if data['current_price'] else "N/A"
        
        analysis_prompt += f"""
{ticker} ({data['name']}):
- Sector: {data['sector']} | Market Cap: {mc_str}
- P/E: {pe_str} | PEG: {peg_str} | Beta: {beta_str}
- Revenue Growth: {rg_str} | Earnings Growth: {eg_str}
- Profit Margin: {pm_str} | 52W Change: {chg_str}
- Analyst Target: {target_str} (Current: {price_str})
"""

    analysis_prompt += """

INSTRUCTIONS:
1. Score each stock 0-100 based on user profile fit
2. Provide 2-3 sentence reasoning for each score
3. List 2-3 key factors (why it's a good fit)
4. List 1-2 risks (concerns or red flags)
5. List 1-2 catalysts (upcoming events or themes)

Return JSON with this EXACT structure:
{
  "TICKER1": {
    "score": 85,
    "reasoning": "Strong fit because...",
    "key_factors": ["Factor 1", "Factor 2"],
    "risks": ["Risk 1"],
    "catalysts": ["Catalyst 1", "Catalyst 2"]
  },
  "TICKER2": {
    "score": 70,
    "reasoning": "...",
    "key_factors": ["..."],
    "risks": ["..."],
    "catalysts": ["..."]
  }
}
"""

    # Call LLM for deep analysis
    try:
        analysis_result = await llm_generate_func(
            analysis_prompt,
            max_tokens=4096,  # Allow long response for deep analysis
        )
        
        if analysis_result and isinstance(analysis_result, dict):
            return analysis_result
        else:
            logger.error("LLM returned invalid analysis format")
            return {}
    except Exception as e:
        logger.error(f"Deep analysis failed: {e}")
        return {}


def _stage3_final_selection(
    stock_analysis: dict[str, dict],
    risk: str,
    goal: str,
    horizon: str
) -> list[str]:
    """
    Stage 3: Select final stocks based on scores and diversification.
    
    Selection criteria:
    - Top scores (but not just top N - consider diversification)
    - Sector balance
    - Risk balance (mix of stable + growth)
    - Complementary, not redundant
    """
    if not stock_analysis:
        return []
    
    # Sort by score
    sorted_stocks = sorted(
        stock_analysis.items(),
        key=lambda x: x[1].get("score", 0),
        reverse=True
    )
    
    # Determine count based on risk
    target_count = {"low": 5, "medium": 6, "high": 8}.get(risk, 6)
    
    # Select top performers
    selected = [ticker for ticker, _ in sorted_stocks[:target_count]]
    
    return selected


def _build_screening_criteria_summary(risk: str, goal: str, horizon: str) -> str:
    """Build human-readable summary of screening criteria"""
    parts = [
        f"Risk: {risk.capitalize()}",
        f"Goal: {goal.capitalize()}",
        f"Horizon: {horizon}",
    ]
    
    if "month" in horizon.lower() or "short" in horizon.lower() or "<" in horizon.lower():
        parts.append("Focus: Momentum, catalysts, timing")
    elif "year" in horizon.lower() and not "5" in horizon and not "10" in horizon:
        parts.append("Focus: Growth trajectory, competitive position")
    else:
        parts.append("Focus: Secular trends, compounding, moat")
    
    return " | ".join(parts)
