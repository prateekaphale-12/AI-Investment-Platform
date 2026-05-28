# AI Investment Research & Portfolio Intelligence Platform

Multi-agent **decision-support** research: deterministic market data + technical indicators in Python, orchestrated with **LangGraph**, AI narrative via **OpenAI or Groq** (user-configured via the AI Settings page). Not a price-prediction or trading product.

## What's implemented

| Area | Status |
|------|--------|
| **Backend** | FastAPI, async jobs, logging, optional **Redis** cache, **SQLite** (default local) or **PostgreSQL** (Docker / `DATABASE_URL`) |
| **Auth** | Register / login, **JWT**; analyses and watchlist are **per user**; list / delete analyses; **PDF export** |
| **Agents** | 8-node LangGraph: Planner → Market → Financial → Technical → News Sentiment → Risk → Portfolio Allocation → Report |
| **API** | Analysis (`/analyze`, status, results, report, history, delete, PDF), watchlist, **daily market snapshot**, stock prices, health / capabilities |
| **Frontend** | Vite + React + TypeScript + Tailwind: auth UI, dashboard, charts, markdown report, watchlist, homepage **daily picks / movers** |
| **Docker** | `docker-compose.yml`: Postgres, Redis, backend (Python 3.12), frontend (nginx + `/api` → backend) |
| **CI** | GitHub Actions: backend tests, frontend build |

See `ARCHITECTURE.md` and `IMPLEMENTATION_PLAN.md` for design detail and roadmap.

## Prerequisites

- **Python 3.12 or 3.13** recommended for local dev (Docker uses 3.12).
- **Node 20+** for the frontend.
- **LLM API key** — configure OpenAI or Groq via the **AI Settings** page in the app after logging in.

**Docker (optional but simplest for Postgres + Redis + full stack)**

- Windows / macOS: Docker Desktop  
- Linux: Docker Engine + Compose plugin

**Security**

- Never commit real API keys or production passwords. Copy `backend/.env.example` → `backend/.env` (gitignored) and fill secrets there.
- The sample `docker-compose.yml` passwords are **for local development only**.
- **`JWT_SECRET_KEY`**: use a long random string in `.env`.

---

## Quick start (Docker — recommended)

```cmd
docker compose up --build
```

- **App UI:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000) — Swagger: [/docs](http://localhost:8000/docs)

After the app starts, go to **AI Settings** in the nav bar and enter your OpenAI or Groq API key.

---

## Quick start (local — no Docker)

### Backend

```cmd
cd backend
copy .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```cmd
cd frontend
npm install
npm run dev
```

---

## API overview

| Method | Path | Notes |
|--------|------|--------|
| GET | `/v1/health` | Liveness |
| GET | `/v1/capabilities` | AI provider status |
| GET | `/v1/market/daily-snapshot` | Daily picks / movers |
| POST | `/v1/auth/register` | Returns `access_token` |
| POST | `/v1/auth/login` | Returns `access_token` |
| POST | `/v1/analyze` | Start analysis (Bearer JWT) |
| GET | `/v1/analysis/{id}/status` | Poll status |
| GET | `/v1/analysis/{id}/results` | Get results |

---

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| **401 on `/analyze`** | Register or login first; send `Authorization: Bearer …` |
| **Port already in use** | Change host port in `docker-compose.yml` |
| **Frontend cannot reach API** | Local: backend on `:8000`, Vite proxy. Docker: use `:3000` |
| **AI badge shows "Configure AI"** | Go to AI Settings page and enter your OpenAI or Groq API key |
| **Startup slow** | First daily snapshot runs in background after DB init — may take 1-2 min |
| **Python 3.14 pip errors** | Use Python **3.12/3.13** or Docker |

---

## Important disclaimers

- Outputs are **research and education only**, not investment, tax, or legal advice.
- "Expected return" labels are **heuristic proxies**, not forecasts.
- Market data depends on **yfinance**; outages and delays are possible.
