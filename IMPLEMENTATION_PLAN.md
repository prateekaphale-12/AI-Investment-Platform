# AI Investment Research & Portfolio Intelligence Platform
## Phased Implementation Plan (Revised)

---

## Core Philosophy

**BUILD VERTICALLY, NOT HORIZONTALLY.**

One complete working flow > 10 half-built features.

**FIRST MVP = One Vertical Slice:**
```
Input Form → Market Agent → Technical Analysis → AI Summary → Frontend Result
```
Ship this. Then expand.

---

## Tech Stack Summary

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.12+ | Core language |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| LangGraph | Agent orchestration graph |
| Pydantic v2 | Data validation |
| SQLAlchemy 2.0 + aiosqlite | ORM + async SQLite |
| yfinance | Stock market data (free) |
| pandas | Data manipulation |
| pandas-ta | Technical indicators |
| httpx | Async HTTP |
| google-generativeai | Gemini for summaries ONLY |
| Loguru | Logging |
| textblob / vaderSentiment | Sentiment analysis |

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18+ | UI Framework |
| TypeScript | Type safety |
| Vite | Build tool |
| Tailwind CSS | Styling |
| Recharts | Charts (only Pie + Line) |
| Axios | HTTP client |
| React Markdown | Report rendering |

### Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker + Docker Compose | Containerization |
| SQLite | Database |
| Git | Version control |

---

## Prerequisites

### System Requirements
- Python 3.12+
- Node.js 20+
- Docker Desktop (optional, for containerized run)

### Google Gemini Setup
1. Go to https://aistudio.google.com/app/apikey
2. Create free API key (no credit card needed)
3. Save in `backend/.env`:
```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.0-flash
```

---

## CRITICAL RULE: Gemini Usage

| Use Gemini For | Do NOT Use Gemini For |
|----------------|----------------------|
| ✅ Investment report generation | ❌ RSI calculation |
| ✅ Natural language summaries | ❌ MACD calculation |
| ✅ "Why This Stock?" explanations | ❌ P/E ratio computation |
| ✅ Executive summary | ❌ Risk scoring |
| | ❌ Sentiment scoring |
| | ❌ Moving averages |
| | ❌ Portfolio allocation math |
| | ❌ Any deterministic calculation |

**All technical/financial analysis = pure Python code.**
**Gemini = text generation only.**

---

## PHASE 1: Backend Foundation (Vertical Slice)

### Goal: One working end-to-end flow from form input to result display

```
User Input → Planner Agent → Market Research Agent → Technical Analysis Agent
  → Report Agent (Gemini summary) → Frontend Display
```

### Steps

| # | Task | Details |
|---|------|---------|
| 1.1 | Project scaffold | Create `backend/` with modular structure |
| 1.2 | Config + .env | Pydantic-settings, `.env.example` |
| 1.3 | Pydantic models | UserInput, StockData, TechIndicators, Report schemas |
| 1.4 | Database models | 3 tables: analysis_sessions, watchlist, stock_cache (raw SQLite, no Alembic) |
| 1.5 | DB init | Simple `init_db.py` that creates tables on startup |
| 1.6 | FastAPI app | App factory, CORS, health endpoint |
| 1.7 | Stock Data Service | yfinance wrapper: fetch prices, info, fundamentals (with cache) |
| 1.8 | Technical Service | pandas-ta: RSI(14), MACD(12,26,9), SMA(20/50/200) — pure Python |
| 1.9 | Sentiment Service (basic) | News headlines → VADER → aggregated score |
| 1.10 | Stock Universe | Pre-defined 30 tickers across 5 sectors |
| 1.11 | Planner Agent | Maps user input (sectors, risk) to ticker universe |
| 1.12 | Market Research Agent | Fetches price + company data for selected tickers |
| 1.13 | Technical Analysis Agent | Calculates indicators for each ticker |
| 1.14 | Report Agent | Gemini generates summary + "Why This Stock?" explanations |
| 1.15 | LangGraph Graph | Chains: Planner → Market → Technical → Report |
| 1.16 | API Endpoint | `POST /api/v1/analyze` + `GET /status` + `GET /results` |
| 1.17 | Verify end-to-end | Backend-only: `curl POST /analyze` → get results |

**Deliverable:**
```
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"budget": 50000, "risk_tolerance": "medium", "investment_horizon": "1y", "interests": ["Technology"], "goal": "growth"}'
→ Returns session_id, status, results with:
  - Stock prices
  - RSI, MACD, SMA values
  - AI-generated report
```

---

## PHASE 2: MVP Frontend

### Goal: Minimal working frontend — no fancy dashboards yet

### MVP Components (ONLY these — no more)

| # | Component | Purpose |
|---|-----------|---------|
| 2.1 | QueryForm | Budget slider, risk dropdown, sector selector, submit button |
| 2.2 | LoadingIndicator | Simple spinner (no complex stepper yet) |
| 2.3 | PortfolioResults | List of stocks with allocation %, amount, expected return |
| 2.4 | AllocationPieChart | Recharts PieChart showing allocation breakdown |
| 2.5 | StockPriceChart | Recharts LineChart with time period toggle (1M/6M/1Y) |
| 2.6 | AIReport | React-Markdown rendering of Gemini-generated report |
| 2.7 | "Why This Stock?" | Expandable cards showing rationale per ticker |

### NOT building in MVP (later):
- ❌ Risk gauge
- ❌ Technical charts (RSI/MACD visualization)
- ❌ News feed
- ❌ Sentiment meter
- ❌ Advanced theme system
- ❌ Loading skeletons

### Component Tree (MVP)
```
App
└── HomePage
    ├── QueryForm
    ├── LoadingIndicator (conditional)
    └── ResultsContainer (conditional)
        ├── PortfolioResults
        │   ├── AllocationPieChart
        │   └── StockCard[]
        │       └── "Why This Stock?" expandable
        ├── StockPriceChart
        └── AIReport
```

### Data Flow
```
Fill form → Submit → POST /api/v1/analyze
  → Show spinner (poll GET /status every 2s)
  → GET /api/v1/analysis/{id}/results
  → Render PortfolioResults + PieChart + PriceChart + AIReport
```

---

## PHASE 3: Watchlist Feature

### Goal: Users can save stocks and revisit past analyses

### Database
```sql
CREATE TABLE watchlist (
    id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES analysis_sessions(id),
    ticker TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API
```
POST   /api/v1/watchlist         → Add stock to watchlist
DELETE /api/v1/watchlist/{ticker} → Remove from watchlist
GET    /api/v1/watchlist          → Get all watched stocks + their last analysis
```

### Frontend
- "Add to Watchlist" button on each stock card
- Watchlist page showing saved stocks + quick view
- Badge showing new analyses available

---

## PHASE 4: "Why This Stock?" Feature

### Goal: Explainability — users see WHY each stock was chosen

### Backend
Each stock in portfolio response includes:
```json
{
  "ticker": "NVDA",
  "allocation_pct": 25,
  "rationale": {
    "market_trend": "Strong upward momentum, up 45% YoY",
    "technical": "RSI 58 (healthy), MACD bullish crossover, above 50-day SMA",
    "sentiment": "Positive analyst ratings (Buy: 38, Hold: 5, Sell: 2)",
    "fundamentals": "P/E 28 (reasonable for sector), Revenue growth 22% YoY",
    "risk": "Moderate volatility (Beta 1.5), but strong financial health (Score: 82)",
    "summary": "NVIDIA selected because of dominant AI/GPU market position, strong earnings momentum, healthy technical indicators, and overwhelmingly positive analyst sentiment."
  }
}
```

The `rationale.summary` is generated by Gemini.
Everything else is computed by Python agents.

### Frontend
- Each PortfolioCard has an expandable "Why This Stock?" section
- Shows bullet points for each factor
- Color-coded: green (positive), red (caution), gray (neutral)

---

## PHASE 5: Agent Memory (Post-MVP)

### Not building now — designing for future

### Future Architecture
```
┌─────────────────────────────────────────┐
│            AGENT MEMORY STORE            │
│  SQLite tables:                          │
│  - user_preferences (risk, sectors, etc) │
│  - analysis_history (past results)       │
│  - watchlist (favorite tickers)          │
│  - feedback (user ratings)               │
│                                          │
│  Agents read/write to memory:            │
│  Planner: reads user_preferences         │
│  Risk: reads analysis_history for trends │
│  Portfolio: reads past allocations       │
└─────────────────────────────────────────┘
```

---

## WHAT WE SKIP INITIALLY (Overengineering)

| Skip This | Reason | Add Later When |
|-----------|--------|----------------|
| Alembic | Raw SQLite is fine for MVP | Need to migrate schema in production |
| Complex LangGraph checkpointing | MemorySaver is enough | Need to resume failed analyses |
| Full test suite | Manual testing first | Codebase stabilizes |
| Multi-stage Docker | Single Dockerfile is fine | Deploying to production |
| Dark/Light theme | One theme is fine | Users request it |
| SSE streaming | Simple polling is fine | Analysis takes > 30s |
| All 8 agents | Only need 4 for MVP | Core flow works |
| All 13 chart components | Only need 2 charts | Users ask for more |

---

## REVISED PHASED PLAN (2-3 weeks)

### Phase 1: Vertical Slice Backend (Days 1-4)
- [ ] Project scaffold + config + DB
- [ ] Stock data service + cache
- [ ] Technical indicators (RSI, MACD, SMA)
- [ ] Basic sentiment (VADER)
- [ ] Planner + Market + Technical agents
- [ ] Report agent (Gemini summary)
- [ ] LangGraph graph (4 nodes)
- [ ] `/analyze` + `/status` + `/results` endpoints
- [ ] Watchlist tables + endpoints

### Phase 2: MVP Frontend (Days 5-8)
- [ ] React + Vite + Tailwind scaffold
- [ ] QueryForm component
- [ ] LoadingIndicator (polling)
- [ ] PortfolioResults (cards + allocation)
- [ ] AllocationPieChart
- [ ] StockPriceChart
- [ ] AIReport (markdown render)
- [ ] "Why This Stock?" expandable cards
- [ ] Watchlist page + "Add to Watchlist" button
- [ ] Wire everything to backend API

### Phase 3: Polish & Docker (Days 9-10)
- [ ] Single Dockerfile + docker-compose.yml
- [ ] Error handling + edge cases
- [ ] Basic tests for core logic
- [ ] README with screenshots
- [ ] Demo video preparation

---

## SUCCESS CRITERIA (MVP)

After Phase 3, the system should:

1. ✅ Accept user input (budget, risk, horizon, sectors, goal)
2. ✅ Fetch real stock data from yfinance
3. ✅ Calculate RSI, MACD, SMA for each stock (pure Python)
4. ✅ Generate AI summary + "Why This Stock?" via Gemini
5. ✅ Display portfolio allocation with pie chart
6. ✅ Show stock price history chart
7. ✅ Allow users to save stocks to watchlist
8. ✅ Run in Docker with `docker compose up`
9. ✅ Feel like a real product, not a demo

---

## REVISED ARCHITECTURE — VERTICAL SLICE

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Browser)                         │
│  QueryForm → Submit → Poll Status → View Results        │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  POST /analyze ───────────────────────────────────────┐ │
│    │ Creates session, returns session_id               │ │
│    │                                                    │ │
│    ▼                                                    │ │
│  LangGraph (4 nodes, sequential):                       │ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │ Planner  │→│  Market  │→│Technical │→│  Report  │  │ │
│  │ (Python) │ │ (Python) │ │ (Python) │ │ (Gemini) │  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│    │                                                    │ │
│    ▼                                                    │ │
│  Save results to SQLite ←───────────────────────────────┘ │
│                                                          │
│  GET /status → Return agent progress                     │
│  GET /results → Return full structured data              │
│  GET /watchlist → Return saved stocks                    │
│                                                          │
│  External APIs:                                          │
│  ├── yfinance (stock data)                               │
│  └── Gemini (report generation only)                     │
└──────────────────────────────────────────────────────────┘
```

---

## KEY METRICS

| Metric | Target |
|--------|--------|
| Total files generated | ~35 |
| Backend Python files | ~20 |
| Frontend React files | ~15 |
| Analysis time | < 15 seconds |
| Lines of code | ~3000-5000 |
| Cost to run | $0 (free APIs only) |
| Time to MVP | 10 days |