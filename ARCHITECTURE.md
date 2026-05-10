# AI Investment Research & Portfolio Intelligence Platform
## System Architecture Document (Revised)

---

## Table of Contents
1. [Core Philosophy](#1-core-philosophy)
2. [System Overview](#2-system-overview)
3. [Backend Architecture](#3-backend-architecture)
4. [Frontend Architecture (MVP)](#4-frontend-architecture-mvp)
5. [LangGraph Agent System](#5-langgraph-agent-system)
6. [Data Flow](#6-data-flow)
7. [Database Schema](#7-database-schema)
8. [API Design](#8-api-design)
9. ["Why This Stock?" Feature](#9-why-this-stock-feature)
10. [Watchlist Feature](#10-watchlist-feature)
11. [Docker Setup](#11-docker-setup)
12. [Post-MVP Roadmap](#12-post-mvp-roadmap)

---

## 1. Core Philosophy

### Build Vertically, Not Horizontally

**WRONG WAY:** Build all agents, all charts, all APIs, all infra before anything works.
Most projects die here.

**CORRECT WAY:** Build one complete flow end-to-end. Ship it. Then expand.

### MVP Vertical Slice
```
User Input → [Planner] → [Market Research] → [Technical Analysis] → [AI Summary] → Frontend
             (Python)     (Python/yfinance)   (Python/pandas-ta)   (Gemini ONLY)
```

### Critical Rule: Gemini Usage

| ✅ Use Gemini For | ❌ Do NOT Use Gemini For |
|-------------------|------------------------|
| Investment report generation | RSI calculation |
| Natural language summaries | MACD calculation |
| "Why This Stock?" explanations | P/E ratio computation |
| Executive summary text | Risk scoring |
| | Sentiment scoring |
| | Moving averages |
| | Portfolio allocation math |
| | Any deterministic calculation |

**All technical/financial analysis = pure Python code.**
**Gemini = text generation only.**

This keeps the system:
- **Cheap** — Gemini free tier covers the tiny text generation usage
- **Reliable** — deterministic calculations never fail due to API issues
- **Consistent** — RSI(14) always returns the same value for the same data
- **Fast** — no API call overhead for core calculations

---

## 2. System Overview

### What This Is
An AI-powered **investment research decision-support system** that:
1. Takes user preferences (budget, risk, sectors, goals)
2. Fetches real market data
3. Calculates technical indicators
4. Analyzes fundamentals
5. Measures sentiment
6. Generates AI-powered explanations + summary

### What This Is NOT
- ❌ Not a stock price predictor
- ❌ Not a trading bot
- ❌ Not financial advice (disclaimer included)

### System Boundaries (MVP)

```
┌──────────────────────────────────────────────────────────┐
│              USER (Browser - React SPA)                   │
│  QueryForm → Results (Charts + Report + Watchlist)       │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP REST (simple polling, no SSE)
┌────────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                         │
│                                                           │
│  POST /analyze → LangGraph (4 agents)                    │
│  GET /status    → Poll progress                           │
│  GET /results   → Full analysis data                      │
│  CRUD /watchlist → Saved stocks                           │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │  LangGraph State Machine                           │   │
│  │                                                    │   │
│  │  [Planner] → [Market] → [Technical] → [Report]    │   │
│  │   Python      yfinance    pandas-ta     Gemini     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  External APIs:                                           │
│  ├── yfinance ── stock prices, info, financials           │
│  └── Gemini ──── report generation ONLY                   │
└───────────────────────────────────────────────────────────┘
```

---

## 3. Backend Architecture

### Folder Structure (MVP)

```
backend/
├── .env.example
├── requirements.txt
├── Dockerfile
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, CORS, lifespan
│   ├── config.py                   # Pydantic-settings (env vars)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py               # Main API router
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── analysis.py     # POST /analyze, GET /status, GET /results
│   │           ├── watchlist.py    # CRUD /watchlist
│   │           └── health.py       # GET /health
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py           # Shared agent utilities
│   │   ├── planner_agent.py        # Maps input → ticker universe
│   │   ├── market_research_agent.py # Fetches yfinance data
│   │   ├── technical_agent.py       # RSI, MACD, SMA (pure Python)
│   │   ├── report_agent.py          # Gemini summary generation
│   │   └── graph/
│   │       ├── __init__.py
│   │       ├── state.py             # AgentState TypedDict
│   │       └── graph.py             # LangGraph builder
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── stock_service.py        # yfinance wrapper + cache
│   │   ├── technical_service.py    # pandas-ta calculations
│   │   ├── sentiment_service.py    # VADER analysis
│   │   └── llm_service.py          # Gemini API wrapper
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── domain.py               # Pydantic schemas
│   │   └── database.py             # SQLite table creation
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── init_db.py              # Create tables on startup
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py               # Loguru logging
│       ├── stock_universe.py       # Pre-defined tickers by sector
│       └── helpers.py              # Utility functions
│
├── data/                           # SQLite database lives here
└── logs/                           # Log files
```

### What We Skip (MVP)
- ❌ Alembic (raw SQLite)
- ❌ Complex checkpointing (MemorySaver only)
- ❌ SSE streaming (simple polling)
- ❌ Celery (in-process asyncio)
- ❌ Multi-stage Docker (single Dockerfile)
- ❌ Full test suite (manual testing)
- ❌ Authentication (no users yet)

---

## 4. Frontend Architecture (MVP)

### MVP Components — ONLY These

| # | Component | File | Purpose |
|---|-----------|------|---------|
| 1 | **QueryForm** | `QueryForm.tsx` | Budget slider, risk dropdown, sector selector (multi), goal input, submit button |
| 2 | **LoadingIndicator** | `LoadingIndicator.tsx` | Simple spinner with "Analyzing..." text; polls `/status` every 2s |
| 3 | **PortfolioResults** | `PortfolioResults.tsx` | List of stock cards with allocation %, amount, expected return |
| 4 | **AllocationPieChart** | `AllocationPieChart.tsx` | Recharts PieChart — shows % breakdown by ticker |
| 5 | **StockPriceChart** | `StockPriceChart.tsx` | Recharts LineChart — price history with 1M/6M/1Y toggle |
| 6 | **WhyThisStock** | `WhyThisStock.tsx` | Expandable card showing per-ticker rationale (bullet points + Gemini summary) |
| 7 | **AIReport** | `AIReport.tsx` | React-Markdown render of full investment report |
| 8 | **WatchlistButton** | `WatchlistButton.tsx` | "Save to Watchlist" toggle on each stock card |

### Component Tree (MVP)
```
App
├── Header (logo + nav: Home, Watchlist)
└── Routes
    ├── HomePage
    │   └── Dashboard
    │       ├── HeroSection (title + tagline)
    │       ├── QueryForm
    │       │   ├── BudgetSlider
    │       │   ├── RiskDropdown
    │       │   ├── SectorMultiSelect
    │       │   ├── GoalDropdown
    │       │   └── SubmitButton
    │       ├── LoadingIndicator (conditional)
    │       └── ResultsContainer (conditional)
    │           ├── SummaryBanner (top-line metrics)
    │           ├── PortfolioResults
    │           │   ├── AllocationPieChart
    │           │   └── StockCard[]
    │           │       ├── Ticker, allocation%, amount
    │           │       ├── WatchlistButton
    │           │       └── WhyThisStock (expandable)
    │           ├── StockPriceChart (ticker selector dropdown)
    │           └── AIReport (markdown)
    │
    ├── WatchlistPage
    │   ├── WatchlistItem[]
    │   └── "Run New Analysis" button
    │
    └── AboutPage
```

### NOT Building in MVP
- ❌ Risk gauge
- ❌ Technical charts (RSI/MACD visualization)
- ❌ News feed
- ❌ Sentiment meter
- ❌ Dark/light theme
- ❌ Loading skeletons
- ❌ SSE streaming
- ❌ Advanced animations

### Tech Stack (MVP Frontend)
```
React 18 + TypeScript
  ├── Vite (build tool)
  ├── Tailwind CSS (utility-first styling)
  ├── Recharts (LineChart + PieChart only)
  ├── Axios (HTTP client)
  ├── React Router DOM (3 routes)
  └── React Markdown (report rendering)
```

### State Management (MVP)

```typescript
// Simple state — no Redux, no Context, no complexity
interface AppState {
  // Analysis
  sessionId: string | null;
  status: 'idle' | 'loading' | 'processing' | 'completed' | 'error';
  results: AnalysisResult | null;
  
  // UI
  selectedTicker: string;
  timeRange: '1M' | '6M' | '1Y';
  
  // Watchlist
  watchlist: string[];
}
```

---

## 5. LangGraph Agent System

### Agent State

```python
# state.py
class AgentState(TypedDict):
    # Input
    session_id: str
    user_input: dict          # budget, risk, horizon, sectors, goal
    
    # Planner output
    stock_universe: list[str]  # tickers to analyze
    strategy: str              # analysis strategy description
    
    # Market Research output
    market_data: dict[str, dict]  # ticker → price, info, beta, sector
    
    # Technical Analysis output
    technical_data: dict[str, dict]  # ticker → RSI, MACD, SMA, signal
    
    # Report output
    report: str                    # Gemini-generated markdown
    
    # Metadata
    errors: list[str]
    status: str                    # running | completed | failed
```

### Graph (4 Nodes, Sequential)

```python
# graph.py
def build_analysis_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    
    # Register nodes
    graph.add_node("planner", planner_node)           # Python
    graph.add_node("market_research", market_node)    # yfinance
    graph.add_node("technical_analysis", technical_node)  # pandas-ta
    graph.add_node("report_generation", report_node)  # Gemini ONLY
    
    # Sequential edges
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "market_research")
    graph.add_edge("market_research", "technical_analysis")
    graph.add_edge("technical_analysis", "report_generation")
    graph.add_edge("report_generation", END)
    
    return graph.compile()
```

### Agent Responsibilities

| Agent | Input | Processing (100% Python) | Output | Gemini? |
|-------|-------|--------------------------|--------|---------|
| **Planner** | UserInput | Parse sectors → map to tickers from stock_universe | `stock_universe: list[str]` | ❌ No |
| **Market Research** | stock_universe | yfinance API calls: prices, company info, beta, sector | `market_data: dict[ticker → data]` | ❌ No |
| **Technical Analysis** | market_data.prices | pandas-ta: RSI(14), MACD(12,26,9), SMA(20/50/200) | `technical_data: dict[ticker → indicators + signal]` | ❌ No |
| **Report** | ALL previous outputs | Construct prompt → Gemini API → parse markdown | `report: str` + `"Why This Stock?"` per ticker | ✅ YES |

### Error Handling Strategy

```
Agent fails → State.errors.append(error_msg)
           → Downstream agents receive partial data
           → Report agent mentions "some data unavailable"
           → Frontend shows warning badge
           → User still gets useful results
```

---

## 6. Data Flow

### Complete Request Lifecycle

```
USER FILLS FORM
  budget: 50000
  risk: medium
  sectors: ["Technology", "Semiconductors"]
  horizon: 1y
  goal: growth
  
  │
  ▼

1. POST /api/v1/analyze
   → Validate input (Pydantic)
   → Generate session_id (UUID)
   → Create DB record: analysis_sessions (status: "processing")
   → Launch background task: run LangGraph
   → Return 202: { session_id, status: "processing" }
  
  │
  ▼

2. FRONTEND: Start polling GET /api/v1/analysis/{session_id}/status (every 2s)
   → Backend: Check LangGraph agent progress
   → Response:
     {
       "status": "processing",
       "current_agent": "market_research",
       "agents_completed": 1,
       "agents_total": 4
     }

  │ (poll until status = "completed" or "failed")
  ▼

3. FRONTEND: GET /api/v1/analysis/{session_id}/results
   → Backend: Fetch from SQLite
   → Response:
     {
       "session_id": "...",
       "status": "completed",
       "summary": {
         "total_budget": 50000,
         "total_expected_return": 9.2,
         "overall_risk": "medium",
         "diversification_score": 68,
         "best_performer": "NVDA",
         "recommended_action": "Invest"
       },
       "market_data": { ... },
       "technical_data": {
         "NVDA": {
           "current_price": 875.50,
           "rsi": 58.2,
           "macd": 12.5,
           "macd_signal": 10.8,
           "sma_20": 845.00,
           "sma_50": 790.00,
           "sma_200": 680.00,
           "signal": "bullish"
         },
         ...
       },
       "portfolio": {
         "allocations": [
           {
             "ticker": "NVDA",
             "allocation_pct": 30,
             "amount": 15000,
             "expected_return": 15.2,
             "risk_score": 45,
             "rationale": {
               "market_trend": "Up 45% YoY, strong AI sector momentum",
               "technical": "RSI 58 (healthy), MACD bullish crossover, above all major SMAs",
               "sentiment": "Very positive (VADER: 0.72), 38 Buy ratings vs 2 Sell",
               "fundamentals": "P/E 28, Revenue growth 22% YoY, Profit margin 42%",
               "risk": "Beta 1.5 (higher volatility), but Financial Health Score: 82 (strong)",
               "summary": "NVIDIA selected as top pick due to dominant AI market position, ..."
             }
           },
           ...
         ]
       },
       "report": "# Investment Research Report\n\n## Executive Summary\n...",
       "report_id": "r-..."
     }

  │
  ▼

4. FRONTEND: Render results
   → SummaryBanner: "Invest $50,000 in 5 stocks | Expected return: 9.2%"
   → AllocationPieChart: Visual breakdown
   → PortfolioResults: Stock cards with WhyThisStock
   → StockPriceChart: Default to NVDA, dropdown to switch
   → AIReport: Full markdown
   → WatchlistButton on each card
```

---

## 7. Database Schema

### Tables (MVP — 4 tables, no migrations)

```sql
-- Analysis sessions
CREATE TABLE IF NOT EXISTS analysis_sessions (
    id TEXT PRIMARY KEY,
    user_input TEXT NOT NULL,           -- JSON string
    status TEXT DEFAULT 'processing',   -- processing | completed | failed
    summary TEXT,                       -- JSON string of summary
    market_data TEXT,                   -- JSON string
    technical_data TEXT,                -- JSON string
    portfolio TEXT,                     -- JSON string
    report TEXT,                        -- Markdown text
    report_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Agent progress (for polling)
CREATE TABLE IF NOT EXISTS agent_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',      -- pending | running | completed | failed
    error TEXT,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

-- Watchlist (saved stocks)
CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    ticker_name TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES analysis_sessions(id)
);

-- Stock cache (avoids hitting yfinance repeatedly)
CREATE TABLE IF NOT EXISTS stock_cache (
    ticker TEXT NOT NULL,
    data_type TEXT NOT NULL,            -- price | info | financials
    data TEXT NOT NULL,                 -- JSON string
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ticker, data_type)
);
```

### Why Not ORM?
For MVP, raw SQLite via `aiosqlite` or even `sqlite3` is simpler and faster. SQLAlchemy adds complexity with no benefit at this scale. We can add it later when we migrate to PostgreSQL.

---

## 8. API Design

### Endpoints (MVP)

| Method | Path | Purpose | Request | Response |
|--------|------|---------|---------|----------|
| `GET` | `/api/v1/health` | Health check | — | `{"status": "ok", "version": "1.0.0"}` |
| `POST` | `/api/v1/analyze` | Submit analysis | UserInput JSON | `{"session_id": "...", "status": "processing"}` |
| `GET` | `/api/v1/analysis/{id}/status` | Poll progress | — | `{"status": "processing", "current_agent": "...", "agents_completed": 2}` |
| `GET` | `/api/v1/analysis/{id}/results` | Get results | — | Full analysis response |
| `GET` | `/api/v1/analysis/{id}/report` | Get report text | — | `{"report_id": "...", "markdown": "..."}` |
| `GET` | `/api/v1/stocks/{ticker}/price` | Get price history | `?period=1y` | Price data array |
| `POST` | `/api/v1/watchlist` | Add to watchlist | `{"session_id": "...", "ticker": "NVDA"}` | `{"status": "added"}` |
| `DELETE` | `/api/v1/watchlist/{ticker}` | Remove from watchlist | — | `{"status": "removed"}` |
| `GET` | `/api/v1/watchlist` | Get watchlist | — | `{"items": [{ticker, session_id, added_at}]}` |

---

## 9. "Why This Stock?" Feature

### Backend Implementation

The Report Agent constructs a rationale for EACH ticker:

```python
# In report_agent.py

def _generate_ticker_rationale(ticker: str, data: dict) -> dict:
    """
    Generate structured rationale for WHY this stock was selected.
    
    Everything is computed from data (Gemini only generates the summary line).
    """
    market = data.get("market", {})
    technical = data.get("technical", {})
    sentiment = data.get("sentiment", {})
    fundamentals = data.get("fundamentals", {})
    risk = data.get("risk", {})
    
    rationale = {
        "market_trend": _describe_market_trend(market),
        "technical": _describe_technical_signals(technical),
        "sentiment": _describe_sentiment(sentiment),
        "fundamentals": _describe_fundamentals(fundamentals),
        "risk": _describe_risk(risk),
        "summary": "PLACEHOLDER"  # Gemini fills this
    }
    
    return rationale
```

The summary line is the ONLY part generated by Gemini:
```
Prompt: "Given these factors about {ticker}:
- Market: {market_trend}
- Technical: {technical}
- Sentiment: {sentiment}
- Fundamentals: {fundamentals}
- Risk: {risk}

Write one sentence explaining why this stock was selected for investment."
```

### Frontend Display

```
┌─────────────────────────────────────────────────┐
│  NVDA  │  25%  │  $12,500  │  Exp. Return: 15.2%│
│                                                  │
│  [Save to Watchlist ★]                           │
│                                                  │
│  ▼ Why This Stock? (click to expand)             │
│                                                  │
│  📈 Market Trend: Up 45% YoY, strong momentum    │
│  📊 Technical: RSI 58 (healthy range),           │
│     MACD bullish crossover, above 50-day SMA    │
│  💬 Sentiment: Very positive (score: 0.72),      │
│     38 Buy / 5 Hold / 2 Sell                     │
│  💰 Fundamentals: P/E 28, Rev growth 22% YoY    │
│  ⚠️  Risk: Beta 1.5 (elevated), but             │
│     Financial Health Score: 82/100 (strong)      │
│                                                  │
│  "NVIDIA selected as top pick due to dominant    │
│   AI market position, strong earnings momentum,  │
│   healthy technical indicators, and positive     │
│   sentiment."                                    │
│                                                  │
│  ✅ Factors: 4 positive, 1 moderate              │
└─────────────────────────────────────────────────┘
```

Color coding:
- 🟢 Green: Positive factor
- 🟡 Yellow: Neutral factor  
- 🔴 Red: Caution factor

---

## 10. Watchlist Feature

### Backend

```python
# watchlist.py endpoints

@router.post("/watchlist")
async def add_to_watchlist(
    body: WatchlistAddRequest,
    db = Depends(get_db)
):
    """Add a ticker to user's watchlist."""
    stmt = """INSERT OR IGNORE INTO watchlist (id, session_id, ticker, ticker_name)
              VALUES (?, ?, ?, ?)"""
    await db.execute(stmt, (str(uuid4()), body.session_id, body.ticker, body.ticker_name))
    await db.commit()
    return {"status": "added"}

@router.delete("/watchlist/{ticker}")
async def remove_from_watchlist(ticker: str, db = Depends(get_db)):
    """Remove a ticker from watchlist."""
    await db.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
    await db.commit()
    return {"status": "removed"}

@router.get("/watchlist")
async def get_watchlist(db = Depends(get_db)):
    """Get all watched stocks."""
    cursor = await db.execute("""
        SELECT w.*, a.summary as last_analysis
        FROM watchlist w
        LEFT JOIN analysis_sessions a ON w.session_id = a.id
        ORDER BY w.added_at DESC
    """)
    rows = await cursor.fetchall()
    return {"items": [dict(row) for row in rows]}
```

### Frontend

```
WatchlistPage
├── Header: "My Watchlist (5 stocks)"
├── WatchlistItem[]
│   ├── Ticker + Company Name
│   ├── Last analyzed: 2 days ago
│   ├── Quick summary from last analysis
│   └── "Analyze Again" button → re-runs analysis with same sectors
└── "Run New Analysis" CTA button
```

---

## 11. Docker Setup

### Single Dockerfile (MVP — not multi-stage)

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create data and logs directories
RUN mkdir -p data logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: "3.9"

services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes:
      - ./backend:/app
      - backend_data:/app/data
    command: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

  frontend:
    build: ./frontend
    ports: ["3000:80"]
    depends_on: [backend]
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1

volumes:
  backend_data:
```

---

## 12. Post-MVP Roadmap

### Phase 2 (Next)
| Feature | Why |
|---------|-----|
| Agent Memory | Remember user preferences, past analyses |
| Full 8-agent system | Financial, Sentiment, Risk, Portfolio agents |
| SSE streaming | Better UX for longer analyses |
| News feed | Show real news per ticker |
| Sentiment meter | Visual sentiment indicator |
| Technical charts | RSI gauge, MACD histogram |

### Phase 3 (Future)
| Feature | Why |
|---------|-----|
| PostgreSQL | Production database |
| Authentication | User accounts |
| PDF export | Downloadable reports |
| Dark mode | User preference |
| Backtesting | Test strategies against history |
| Mobile responsive | Tablet + phone support |

### What Makes This a "Real Product"

| Feature | Status |
|---------|--------|
| ✅ Core analysis working | MVP |
| ✅ "Why This Stock?" explainability | MVP |
| ✅ Watchlist (save favorites) | MVP |
| ✅ AI-generated report | MVP |
| ✅ Dockerized | MVP |
| 🔄 Agent memory | Phase 2 |
| 🔄 User accounts | Phase 3 |
| 🔄 Historical tracking | Phase 3 |