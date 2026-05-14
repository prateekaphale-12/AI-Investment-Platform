from __future__ import annotations

from typing import Any

import asyncpg
from langgraph.graph import END, START, StateGraph

from app.agents.graph.nodes import (
    financial_analysis_node,
    market_research_node,
    news_sentiment_node,
    planner_node,
    portfolio_allocation_node,
    report_generation_node,
    risk_analysis_node,
    technical_analysis_node,
)
from app.agents.graph.state import AgentState


def build_analysis_graph() -> Any:
    g = StateGraph(AgentState)
    g.add_node("planner", planner_node)
    g.add_node("market_research", market_research_node)
    g.add_node("financial_analysis", financial_analysis_node)
    g.add_node("technical_analysis", technical_analysis_node)
    g.add_node("news_sentiment", news_sentiment_node)
    g.add_node("risk_analysis", risk_analysis_node)
    g.add_node("portfolio_allocation", portfolio_allocation_node)
    g.add_node("report_generation", report_generation_node)

    g.add_edge(START, "planner")
    g.add_edge("planner", "market_research")
    g.add_edge("market_research", "financial_analysis")
    g.add_edge("financial_analysis", "technical_analysis")
    g.add_edge("technical_analysis", "news_sentiment")
    g.add_edge("news_sentiment", "risk_analysis")
    g.add_edge("risk_analysis", "portfolio_allocation")
    g.add_edge("portfolio_allocation", "report_generation")
    g.add_edge("report_generation", END)

    return g.compile()


async def run_graph(
    db: asyncpg.Connection,
    session_id: str,
    user_input: dict[str, Any],
    llm_settings: dict[str, Any] = None,
) -> AgentState:
    graph = build_analysis_graph()
    initial: AgentState = {
        "session_id": session_id,
        "user_input": user_input,
        "errors": [],
        "llm_settings": llm_settings or {},
    }
    cfg = {"configurable": {"db": db, "session_id": session_id}}
    out = await graph.ainvoke(initial, config=cfg)
    return out
