from __future__ import annotations

import asyncio
from typing import Any

import aiosqlite
from langchain_core.runnables import RunnableConfig
from loguru import logger

from app.agents.graph.state import AgentState
from app.services import analysis_db as adb
from app.services.llm_service import (
    generate_investment_report,
    generate_json_object,
    generate_ticker_summaries,
)
from app.services.portfolio_service import build_allocations
from app.services.rationale_builder import (
    describe_fundamentals,
    describe_market_trend,
    describe_risk,
    describe_sentiment,
    describe_technical,
)
from app.services.sentiment_service import analyze_headline_sentiment
from app.services.stock_service import build_market_row, fetch_price_history
from app.services.technical_service import compute_indicators
from app.utils.stock_universe import available_sectors, tickers_for_interests


def _cfg(config: RunnableConfig) -> tuple[aiosqlite.Connection, str]:
    c = config["configurable"]
    return c["db"], c["session_id"]


async def planner_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "planner", "running")
    try:
        ui = state.get("user_input") or {}
        interests = ui.get("interests") or []
        risk = ui.get("risk_tolerance") or "medium"
        normalized_interests = list(interests)
        ai_reason = ""
        ai_norm = await generate_json_object(
            (
                "Normalize investment interests to sector labels from allowed list.\n"
                f"Allowed sectors: {available_sectors()}.\n"
                f"Input interests: {interests}\n"
                f"Goal: {ui.get('goal')}; horizon: {ui.get('investment_horizon')}; risk: {risk}\n"
                'Return object: {"normalized_interests": ["..."], "reason": "..."}'
            )
        )
        if ai_norm:
            candidate = ai_norm.get("normalized_interests")
            if isinstance(candidate, list):
                filtered = [str(x).strip().lower() for x in candidate if str(x).strip().lower() in available_sectors()]
                if filtered:
                    normalized_interests = filtered
            ai_reason = str(ai_norm.get("reason", "")).strip()
        picks = tickers_for_interests(normalized_interests)
        cap = {"low": 5, "medium": 6, "high": 8}.get(risk, 6)
        universe = picks[:cap]
        strategy = (
            f"Universe of {len(universe)} liquid US equities aligned to interests {normalized_interests!r} "
            f"and {risk} risk posture."
        )
        if ai_reason:
            strategy += f" AI planning rationale: {ai_reason}"
        await adb.set_agent_status(db, session_id, "planner", "completed")
        return {"stock_universe": universe, "strategy": strategy}
    except Exception as e:
        logger.exception("planner_node: {}", e)
        await adb.set_agent_status(db, session_id, "planner", "failed", str(e))
        return {"stock_universe": [], "strategy": "", "errors": [f"planner: {e!s}"], "status": "failed"}


async def market_research_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "market_research", "running")
    try:
        tickers = state.get("stock_universe") or []
        if not tickers:
            await adb.set_agent_status(db, session_id, "market_research", "completed")
            return {"market_data": {}}

        rows = await asyncio.gather(*(build_market_row(db, t) for t in tickers))
        market_data = {r["ticker"]: r for r in rows}
        await adb.set_agent_status(db, session_id, "market_research", "completed")
        return {"market_data": market_data}
    except Exception as e:
        logger.exception("market_research_node: {}", e)
        await adb.set_agent_status(db, session_id, "market_research", "failed", str(e))
        return {"market_data": {}, "errors": [f"market_research: {e!s}"]}


async def technical_analysis_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "technical_analysis", "running")
    technical_data: dict[str, dict] = {}
    try:
        tickers = state.get("stock_universe") or []
        market_data = state.get("market_data") or {}

        async def _one(ticker: str) -> tuple[str, dict]:
            df = await fetch_price_history(db, ticker, "1y")
            tech = compute_indicators(df)
            mrow = market_data.get(ticker) or {}
            if mrow.get("current_price") and not tech.get("current_price"):
                tech["current_price"] = mrow["current_price"]
            return ticker, tech

        if tickers:
            pairs = await asyncio.gather(*(_one(t) for t in tickers))
            technical_data = {k: v for k, v in pairs}

        await adb.set_agent_status(db, session_id, "technical_analysis", "completed")
        return {"technical_data": technical_data}
    except Exception as e:
        logger.exception("technical_analysis_node: {}", e)
        await adb.set_agent_status(db, session_id, "technical_analysis", "failed", str(e))
        return {"technical_data": technical_data, "errors": [f"technical_analysis: {e!s}"]}


async def financial_analysis_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "financial_analysis", "running")
    try:
        market_data = state.get("market_data") or {}
        financial_data: dict[str, dict] = {}
        for ticker, m in market_data.items():
            info = (m.get("info") or {}) if isinstance(m.get("info"), dict) else {}
            rg = info.get("revenueGrowth")
            pm = info.get("profitMargins")
            pe = info.get("trailingPE")
            quality = 50.0
            if isinstance(rg, (int, float)):
                quality += max(-15.0, min(20.0, float(rg) * 100 / 4))
            if isinstance(pm, (int, float)):
                quality += max(-10.0, min(20.0, float(pm) * 100 / 3))
            if isinstance(pe, (int, float)):
                quality += 8 if 8 <= float(pe) <= 35 else -6
            financial_data[ticker] = {
                "quality_score": round(max(0.0, min(100.0, quality)), 1),
                "trailing_pe": pe,
                "revenue_growth": rg,
                "profit_margin": pm,
            }
            ai_fin = await generate_json_object(
                (
                    f"Ticker: {ticker}\n"
                    f"Facts: quality_score={financial_data[ticker]['quality_score']}, "
                    f"trailing_pe={pe}, revenue_growth={rg}, profit_margin={pm}\n"
                    'Return: {"financial_view":"bullish|neutral|cautious","commentary":"<=25 words"}'
                ),
                max_tokens=512,
            )
            if ai_fin:
                financial_data[ticker]["financial_view"] = str(ai_fin.get("financial_view", "neutral")).lower()
                financial_data[ticker]["commentary"] = str(ai_fin.get("commentary", ""))[:220]
        await adb.set_agent_status(db, session_id, "financial_analysis", "completed")
        return {"financial_data": financial_data}
    except Exception as e:
        logger.exception("financial_analysis_node: {}", e)
        await adb.set_agent_status(db, session_id, "financial_analysis", "failed", str(e))
        return {"financial_data": {}, "errors": [f"financial_analysis: {e!s}"]}


async def news_sentiment_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "news_sentiment", "running")
    try:
        tickers = state.get("stock_universe") or []
        sentiments = await asyncio.gather(*(analyze_headline_sentiment(t) for t in tickers))
        sentiment_data = {t: s for t, s in zip(tickers, sentiments, strict=True)}
        for t in tickers:
            s = sentiment_data.get(t) or {}
            ai_news = await generate_json_object(
                (
                    f"Ticker: {t}\n"
                    f"Sentiment facts: label={s.get('label')}, compound={s.get('compound')}, headlines_used={s.get('headlines_used')}\n"
                    'Return: {"event_summary":"short","risk_flag":"low|medium|high"}'
                ),
                max_tokens=384,
            )
            if ai_news:
                s["event_summary"] = str(ai_news.get("event_summary", ""))[:220]
                s["risk_flag"] = str(ai_news.get("risk_flag", "medium")).lower()
                sentiment_data[t] = s
        await adb.set_agent_status(db, session_id, "news_sentiment", "completed")
        return {"sentiment_data": sentiment_data}
    except Exception as e:
        logger.exception("news_sentiment_node: {}", e)
        await adb.set_agent_status(db, session_id, "news_sentiment", "failed", str(e))
        return {"sentiment_data": {}, "errors": [f"news_sentiment: {e!s}"]}


async def risk_analysis_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "risk_analysis", "running")
    try:
        market_data = state.get("market_data") or {}
        technical_data = state.get("technical_data") or {}
        risk_data: dict[str, dict] = {}
        sentiment_data = state.get("sentiment_data") or {}
        for ticker, m in market_data.items():
            info = (m.get("info") or {}) if isinstance(m.get("info"), dict) else {}
            beta = info.get("beta")
            signal = (technical_data.get(ticker) or {}).get("signal", "neutral")
            sent = (sentiment_data.get(ticker) or {}).get("label", "neutral")
            score = 45.0
            if isinstance(beta, (int, float)):
                score += float(beta) * 20 - 20
            if signal == "bearish":
                score += 8
            elif signal == "bullish":
                score -= 4
            if sent == "negative":
                score += 5
            elif sent == "positive":
                score -= 2
            risk_data[ticker] = {"risk_score": round(max(0.0, min(100.0, score)), 1), "beta": beta}
            ai_risk = await generate_json_object(
                (
                    f"Ticker: {ticker}\n"
                    f"Facts: beta={beta}, technical_signal={signal}, sentiment_label={sent}, risk_score={risk_data[ticker]['risk_score']}\n"
                    'Return: {"scenario_note":"one short sentence","risk_band":"low|medium|high"}'
                ),
                max_tokens=320,
            )
            if ai_risk:
                risk_data[ticker]["scenario_note"] = str(ai_risk.get("scenario_note", ""))[:200]
                risk_data[ticker]["risk_band"] = str(ai_risk.get("risk_band", "medium")).lower()
        await adb.set_agent_status(db, session_id, "risk_analysis", "completed")
        return {"risk_data": risk_data}
    except Exception as e:
        logger.exception("risk_analysis_node: {}", e)
        await adb.set_agent_status(db, session_id, "risk_analysis", "failed", str(e))
        return {"risk_data": {}, "errors": [f"risk_analysis: {e!s}"]}


async def portfolio_allocation_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "portfolio_allocation", "running")
    ui = state.get("user_input") or {}
    budget = float(ui.get("budget") or 0)
    risk = ui.get("risk_tolerance") or "medium"
    tickers = state.get("stock_universe") or []
    market_data = state.get("market_data") or {}
    technical_data = state.get("technical_data") or {}
    sentiment_data = state.get("sentiment_data") or {}
    financial_data = state.get("financial_data") or {}
    risk_data = state.get("risk_data") or {}
    try:
        rows_for_portfolio: list[dict[str, Any]] = []
        for t in tickers:
            m = market_data.get(t) or {}
            tech = technical_data.get(t) or {}
            sent = sentiment_data.get(t) or {}
            info = (m.get("info") or {}) if isinstance(m.get("info"), dict) else {}
            fin = financial_data.get(t) or {}
            risk_row = risk_data.get(t) or {}
            rationale = {
                "market_trend": describe_market_trend(m),
                "technical": describe_technical(tech),
                "sentiment": describe_sentiment(sent) + (f"; event: {sent.get('event_summary')}" if sent.get("event_summary") else ""),
                "fundamentals": describe_fundamentals(info) + f"; quality_score {fin.get('quality_score')}",
                "risk": describe_risk(info, tech) + (f"; scenario: {risk_row.get('scenario_note')}" if risk_row.get("scenario_note") else ""),
                "summary": "",
            }
            rows_for_portfolio.append(
                {"ticker": t, "market": m, "technical": tech, "sentiment": sent, "rationale": rationale}
            )

        valid_rows = [
            r
            for r in rows_for_portfolio
            if not (r.get("market") or {}).get("error")
            and (r.get("market") or {}).get("current_price") is not None
        ]
        use_rows = valid_rows if valid_rows else rows_for_portfolio
        allocations_list, summary = build_allocations(
            budget,
            risk,
            [
                {
                    "ticker": r["ticker"],
                    "market": r["market"],
                    "technical": r["technical"],
                    "sentiment": r["sentiment"],
                    "rationale": r["rationale"],
                }
                for r in use_rows
            ],
        )
        ai_decision = await generate_json_object(
            (
                f"Budget={budget}, risk={risk}, goal={ui.get('goal')}, horizon={ui.get('investment_horizon')}\n"
                f"Allocations={allocations_list}\n"
                'Return: {"advisor_note":"<=40 words", "confidence":"low|medium|high"}'
            ),
            max_tokens=512,
        )
        if ai_decision:
            summary["advisor_note"] = str(ai_decision.get("advisor_note", ""))[:320]
            summary["ai_confidence"] = str(ai_decision.get("confidence", "medium")).lower()
        await adb.set_agent_status(db, session_id, "portfolio_allocation", "completed")
        return {"portfolio": {"allocations": allocations_list}, "summary": summary}
    except Exception as e:
        logger.exception("portfolio_allocation_node: {}", e)
        await adb.set_agent_status(db, session_id, "portfolio_allocation", "failed", str(e))
        return {"portfolio": {"allocations": []}, "summary": None, "errors": [f"portfolio_allocation: {e!s}"]}


def _merge_summary_lines(raw: str, tickers: list[str]) -> dict[str, str]:
    """Parse 'TICKER: sentence' lines from model output."""
    out: dict[str, str] = {t: "" for t in tickers}
    for line in raw.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        ticker, _, rest = line.partition(":")
        t = ticker.strip().upper()
        if t in out:
            out[t] = rest.strip()
    return out


async def report_generation_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db, session_id = _cfg(config)
    await adb.set_agent_status(db, session_id, "report_generation", "running")

    ui = state.get("user_input") or {}
    budget = float(ui.get("budget") or 0)
    tickers = state.get("stock_universe") or []
    market_data = state.get("market_data") or {}
    technical_data = state.get("technical_data") or {}
    sentiment_data = state.get("sentiment_data") or {}
    portfolio_payload = state.get("portfolio") or {"allocations": []}
    allocations_list = portfolio_payload.get("allocations", [])
    summary = state.get("summary")

    try:
        if not tickers:
            await adb.finalize_session(
                db,
                session_id,
                status="failed",
                summary={"error": "No tickers to analyze"},
                market_data={},
                technical_data={},
                portfolio={"allocations": []},
                report="No analysis generated — planner returned empty universe.",
                report_id=f"r-{session_id[:8]}",
            )
            await adb.set_agent_status(db, session_id, "report_generation", "completed")
            return {"errors": ["empty stock universe"], "status": "failed", "portfolio": {"allocations": []}}

        batch_lines = []
        for row in allocations_list:
            ticker = row["ticker"]
            rat = row.get("rationale") or {}
            batch_lines.append(
                f"{ticker}: market={rat.get('market_trend','')} | tech={rat.get('technical','')} | "
                f"sent={rat.get('sentiment','')} | fund={rat.get('fundamentals','')} | risk={rat.get('risk','')}"
            )
        summaries_prompt = (
            "For each ticker line below, reply with one line ONLY in the format TICKER: one concise sentence "
            "explaining inclusion (no invented numbers).\n\n" + "\n".join(batch_lines)
        )
        summaries_raw = await generate_ticker_summaries(summaries_prompt)
        merged = _merge_summary_lines(summaries_raw, [r["ticker"] for r in allocations_list])
        for row in allocations_list:
            rationale = row.get("rationale") or {}
            rationale["summary"] = merged.get(row["ticker"]) or rationale.get("market_trend", "")
            row["rationale"] = rationale

        portfolio_payload = {"allocations": allocations_list}
        if summary is None:
            summary = {
                "total_budget": budget,
                "total_expected_return": 0.0,
                "overall_risk": ui.get("risk_tolerance", "medium"),
                "diversification_score": 0.0,
                "best_performer": tickers[0] if tickers else None,
                "recommended_action": "Research & due diligence only — not investment advice.",
            }

        facts_block = []
        facts_block.append(
            f"Budget: ${budget:,.2f}; risk: {ui.get('risk_tolerance')}; goal: {ui.get('goal')}.\nStrategy: {state.get('strategy','')}"
        )
        facts_block.append("Allocations:")
        for a in allocations_list:
            facts_block.append(
                f"- {a['ticker']}: {a['allocation_pct']}% (~${a['amount']:,.2f}), "
                f"heuristic return proxy {a['expected_return']}%, risk score {a['risk_score']}."
            )
            r = a.get("rationale", {})
            facts_block.append(f"  Rationale bullets: market: {r.get('market_trend')}")
            facts_block.append(f"  Technical: {r.get('technical')}")
            facts_block.append(f"  Sentiment: {r.get('sentiment')}")
            facts_block.append(f"  Fundamentals: {r.get('fundamentals')}")
            facts_block.append(f"  Risk: {r.get('risk')}")
            facts_block.append(f"  Summary: {r.get('summary')}")

        markdown_prompt = (
            "Write a polished **investment research memo** in Markdown.\n"
            "Rules: clarify this is decision-support research, NOT financial advice, NOT price prediction.\n"
            "Use only facts from the data block below; add an Executive Summary and per-ticker section.\n\n"
            "<DATA>\n" + "\n".join(facts_block) + "\n</DATA>\n"
        )
        # Get user's LLM settings
        llm_settings = state.get("llm_settings", {})
        provider_str = llm_settings.get("provider", "groq")
        api_key = None
        
        # Convert string to LLMProvider enum
        from app.services.llm_service import LLMProvider
        if provider_str == "groq":
            provider = LLMProvider.GROQ
        elif provider_str == "openai":
            provider = LLMProvider.OPENAI
        else:
            provider = LLMProvider.GROQ  # default to groq
        
        # Extract API key from user's saved settings
        if provider_str in llm_settings.get("settings", {}):
            api_key = llm_settings["settings"][provider_str].get("api_key")
        
        if not api_key:
            raise ValueError("API key is required for report generation")
        
        report = await generate_investment_report(markdown_prompt, provider=provider, api_key=api_key)
        report_id = f"r-{session_id[:8]}"

        await adb.finalize_session(
            db,
            session_id,
            status="completed",
            summary=summary,
            market_data=market_data,
            technical_data=technical_data,
            portfolio=portfolio_payload,
            report=report,
            report_id=report_id,
        )
        await adb.set_agent_status(db, session_id, "report_generation", "completed")
        return {
            "portfolio": portfolio_payload,
            "summary": summary,
            "report": report,
            "report_id": report_id,
            "sentiment_data": sentiment_data,
            "status": "completed",
        }
    except Exception as e:
        logger.exception("report_generation_node: {}", e)
        await adb.finalize_session(
            db,
            session_id,
            status="failed",
            summary={"error": str(e)},
            market_data=market_data,
            technical_data=technical_data,
            portfolio={},
            report="",
            report_id="",
        )
        await adb.set_agent_status(db, session_id, "report_generation", "failed", str(e))
        return {"errors": [f"report_generation: {e!s}"], "status": "failed", "sentiment_data": sentiment_data}
