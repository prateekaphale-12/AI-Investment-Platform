from __future__ import annotations

import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    user_input: dict

    stock_universe: list[str]
    strategy: str

    market_data: dict[str, dict]
    financial_data: dict[str, dict]
    technical_data: dict[str, dict]
    sentiment_data: dict[str, dict]
    risk_data: dict[str, dict]

    portfolio: dict
    summary: dict
    report: str
    report_id: str

    errors: Annotated[list[str], operator.add]
    status: str
