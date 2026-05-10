# AI Investment Research & Portfolio Intelligence Platform

Multi-agent **decision-support** research: deterministic market data + technical indicators in Python, orchestrated with **LangGraph**, narrative via **Google Gemini** (text only — no LLM math). Not a price-prediction or trading product.

## What’s implemented

| Area | Status |
|------|--------|
| **Backend (Phase 1)** | FastAPI, SQLite (`analysis_sessions`, `agent_progress`, `watchlist`, `stock_cache`), Pydantic models, async background analysis |
| **Agents** | 8-node LangGraph: Planner → Market → Financial → Technical → News Sentiment → Risk → Portfolio Allocation → Report |
| **API** | `POST /api/v1/analyze`, `GET .../status`, `GET .../results`, `GET .../report`, `GET /api/v1/stocks/{ticker}/price`, watchlist + health |
| **Frontend (Phase 2)** | Vite + React + TypeScript + Tailwind: query form, status polling, pie + line charts (Recharts), markdown report, expandable “Why this stock?”, watchlist |
| **Docker (Phase 3)** | `docker-compose.yml`: backend (Python 3.12), frontend (nginx + `/api` proxy to backend) |
| **Quality gate (Next Step)** | Backend `pytest` tests + GitHub Actions CI (backend tests + frontend build) |

See `ARCHITECTURE.md` and `IMPLEMENTATION_PLAN.md` for full product design and roadmap.

## Prerequisites

- **Python 3.12 or 3.13** recommended for local dev (Docker uses 3.12). On **Python 3.14+**, install deps manually if a wheel fails; prefer Docker or 3.12/3.13.
- **Node 20+** for the frontend.
- **Gemini API key** (optional but recommended for polished narratives): [Google AI Studio](https://aistudio.google.com/app/apikey).  
  The backend uses the official **`google-genai`** SDK (not the deprecated `google-generativeai` package).
- **Docker** (optional, recommended for easiest setup):
  - Windows/macOS: Docker Desktop
  - Linux: Docker Engine + Compose plugin

**Security:** never commit API keys, and never paste them into public chats or tickets. Keep them in `backend/.env` (gitignored) or your secret manager. If a key is exposed, revoke it in AI Studio and create a new one.

## Clone and branch

```cmd
git clone https://github.com/prateekaphale-12/AI-Investment-Platform.git
cd AI-Investment-Platform
git checkout feature/hybrid-8-agent-ai
```

## Run option A: Local (no Docker)

### Backend

```cmd
cd backend
copy .env.example .env
# Edit .env: set GEMINI_API_KEY and optionally GEMINI_MODEL, CORS_ORIGINS
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: `http://localhost:8000` — OpenAPI: `/docs`
- SQLite DB path: `backend/data/app.db` (created on startup)

### Frontend

```cmd
cd frontend
npm install
npm run dev
```

- UI: `http://localhost:5173` — Vite proxies `/api` to port `8000`.

### Smoke test

```cmd
curl -X POST http://localhost:8000/api/v1/analyze -H "Content-Type: application/json" -d "{\"budget\":50000,\"risk_tolerance\":\"medium\",\"investment_horizon\":\"1y\",\"interests\":[\"Technology\"],\"goal\":\"growth\"}"
```

Then poll `GET /api/v1/analysis/{session_id}/status` until `completed`, then `GET /api/v1/analysis/{session_id}/results`.

## Run option B: Docker (recommended)

### 1) Install/verify Docker

```cmd
docker --version
docker compose version
```

If these fail, install Docker Desktop (Windows/macOS) or Docker Engine + Compose plugin (Linux), then retry.

### 2) Start stack

From the repo root (set `GEMINI_API_KEY` in your shell or a `.env` file next to `docker-compose.yml`):

```cmd
set GEMINI_API_KEY=your-key
docker compose up --build
```

- Frontend + API through nginx: `http://localhost:3000` (browser calls `/api/...`, nginx proxies to the backend).
- Backend directly: `http://localhost:8000`.

### 3) Useful Docker commands

```cmd
# detached mode
docker compose up -d --build

# logs
docker compose logs -f

# stop
docker compose down

# stop + remove DB volume (clean slate)
docker compose down -v
```

## Verify end-to-end quickly

### Health check
```cmd
curl http://localhost:8000/api/v1/health
```

### Capabilities check (Gemini configured?)
```cmd
curl http://localhost:8000/api/v1/capabilities
```

### Analyze request
```cmd
curl -X POST http://localhost:8000/api/v1/analyze -H "Content-Type: application/json" -d "{\"budget\":50000,\"risk_tolerance\":\"medium\",\"investment_horizon\":\"1y\",\"interests\":[\"Technology\",\"Semiconductors\"],\"goal\":\"growth\"}"
```

Take returned `session_id`, then:
```cmd
curl http://localhost:8000/api/v1/analysis/<session_id>/status
curl http://localhost:8000/api/v1/analysis/<session_id>/results
```

## Tests

```cmd
cd backend
python -m pytest -q
```

Current coverage includes core deterministic logic:
- indicator computation shape and empty-input handling
- portfolio allocation math (percent/amount totals and summary behavior)
- API happy-path + not-found behavior for analysis endpoints

## Important disclaimers

- Outputs are **research and education only**, not investment, tax, or legal advice.
- “Expected return” and similar fields are **heuristic / momentum-style proxies**, not forecasts.
- Market data depends on **yfinance**; availability and rate limits apply.

## Without `GEMINI_API_KEY`

You still get **real market data**, **technical indicators**, **rule-based allocations**, **charts**, and deterministic rationale fields. Gemini-enhanced narrative/commentary degrades gracefully to fallback mode.

## Troubleshooting

- **Port already in use**
  - Change port in run command or stop conflicting process.
- **Frontend cannot reach backend**
  - Local mode: ensure backend running on `8000`.
  - Docker mode: use `http://localhost:3000` (nginx proxies `/api`).
- **Gemini not being used**
  - Check `GET /api/v1/capabilities` → `gemini_configured: true`.
  - Ensure `backend/.env` has valid `GEMINI_API_KEY`, then restart backend.
- **Python 3.14 dependency issues**
  - Prefer Docker or Python 3.12/3.13 for local development.

## License

See `LICENSE`.
