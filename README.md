# AI Investment Research & Portfolio Intelligence Platform

Multi-agent **decision-support** research: deterministic market data + technical indicators in Python, orchestrated with **LangGraph**, narrative via **Google Gemini** (text only — no LLM math). Not a price-prediction or trading product.

## What’s implemented

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

- **Python 3.12 or 3.13** recommended for local dev (Docker uses 3.12). On **Python 3.14+**, pip may lack wheels for some packages; prefer Docker or **3.12/3.13**.
- **Node 20+** for the frontend.
- **Gemini API key** (optional; improves narrative text): [Google AI Studio](https://aistudio.google.com/app/apikey).  
  Backend uses **`google-genai`** (not the deprecated `google-generativeai` package).

**Docker (optional but simplest for Postgres + Redis + full stack)**

- Windows / macOS: Docker Desktop  
- Linux: Docker Engine + Compose plugin

**Security**

- Never commit real API keys or production passwords. Copy `backend/.env.example` → `backend/.env` (gitignored) and fill secrets there.
- The sample `docker-compose.yml` passwords are **for local development only**. Change them before any shared or production deployment.
- **`JWT_SECRET_KEY`**: use a long random string in `.env`; do not ship the default beyond local experiments.

---

## Clone the repository

```cmd
git clone https://github.com/prateekaphale-12/AI-Investment-Platform.git
cd AI-Investment-Platform
```

Use `main`, or checkout a feature branch if the README directs you there.

---

## Quick start (Docker — recommended)

Brings up **PostgreSQL**, **Redis**, backend, and frontend with one command.

### 1) Environment

Docker Compose reads a **repo root** `.env` file for substitutions (tracked template: `.env.example`):

```cmd
copy .env.example .env
```

Edit `.env` and set **`GEMINI_API_KEY`**. Optionally set **`GEMINI_MODEL`**.

Alternatively, set variables in your shell before `docker compose up` (Unix: `export GEMINI_API_KEY=…`).

### 2) Start

```cmd
docker compose up --build
```

- **App UI (nginx + API proxy):** [http://localhost:3000](http://localhost:3000)
- **Backend API only:** [http://localhost:8000](http://localhost:8000) — Swagger: [/docs](http://localhost:8000/docs)
- **Postgres:** host `localhost`, port **`5433`** (mapped from container `5432`)
- **Redis:** host `localhost`, port **`6379`**

The backend container uses Postgres via `DATABASE_URL` and Redis for caching (Compose sets both).

### 3) Useful commands

```cmd
docker compose up -d --build
docker compose logs -f backend
docker compose down
docker compose down -v
```

`down -v` removes named volumes (**wipes Postgres/Redis/backend app data**).

---

## Quick start (local — no Docker)

### Backend

```cmd
cd backend
copy .env.example .env
```

Edit `backend/.env` at minimum:

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Optional; Gemini narratives when set |
| `JWT_SECRET_KEY` | **Required beyond toy use** — random secret for signing JWTs |
| `CORS_ORIGINS` | Frontend origins (default includes Vite `5173` and Docker UI `3000`) |
| `DATABASE_PATH` | SQLite file (relative to **`backend`** cwd); default `data/app.db` |
| `DATABASE_URL` | Leave **empty** for SQLite. Set to a Postgres URL to use Postgres locally |
| `REDIS_URL` | Default `redis://localhost:6379/0`. If Redis is not running, the app still starts; cache calls no-op gracefully |

Install and run:

```cmd
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: [http://localhost:8000](http://localhost:8000) — OpenAPI: [/docs](http://localhost:8000/docs)
- SQLite file: `backend\data\app.db` (created on startup)

**Optional Redis (local):** install Redis locally or run `docker compose up -d redis` from the repo root and keep `REDIS_URL` pointing at `localhost:6379`.

### Frontend

```cmd
cd frontend
npm install
npm run dev
```

- UI: [http://localhost:5173](http://localhost:5173) — dev server proxies `/api` → `http://localhost:8000`.

### Typical user flow after clone

1. Start **backend**, then **frontend** (or use Docker UI on `:3000`).
2. Open the app → **Register** or **Login** (JWT is stored in the browser).
3. Submit an analysis request; poll status until completed; open results / report / export PDF from the UI.
4. Homepage loads **today’s snapshot** when the backend is up (`GET /api/v1/market/daily-snapshot`).

---

## API overview

All routes are prefixed with **`/api`**.

### Public / no auth

| Method | Path | Notes |
|--------|------|--------|
| GET | `/v1/health` | Liveness |
| GET | `/v1/capabilities` | Gemini configured flag |
| GET | `/v1/market/daily-snapshot` | Daily picks / movers (generated on startup schedule + refreshed periodically) |

### Auth

| Method | Path | Notes |
|--------|------|--------|
| POST | `/v1/auth/register` | JSON: `email`, `password` (min 8 chars); returns **`access_token`** |
| POST | `/v1/auth/login` | Same shape; returns token |
| GET | `/v1/auth/me` | Header: `Authorization: Bearer <token>` |

### Protected (Bearer JWT)

| Area | Paths |
|------|--------|
| Analysis | `POST /v1/analyze`, `GET /v1/analysis`, `GET /v1/analysis/{session_id}/status`, `/results`, `/report`, `DELETE /v1/analysis/{session_id}`, `GET …/export/pdf` |
| Watchlist | `GET /v1/watchlist`, `POST /v1/watchlist`, `DELETE /v1/watchlist/{ticker}` |
| Stock | `GET /v1/stocks/{ticker}/price` |

Use **Swagger** at `/docs`: click **Authorize**, enter `Bearer <your_token>`.

### Example (register + analyze) — CMD

Adjust email/password and JSON body as needed.

```cmd
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d "{\"email\":\"you@example.com\",\"password\":\"longpassword123\"}"
```

Copy `access_token` from the JSON response, then:

```cmd
curl -X POST http://localhost:8000/api/v1/analyze -H "Content-Type: application/json" -H "Authorization: Bearer PASTE_TOKEN_HERE" -d "{\"budget\":50000,\"risk_tolerance\":\"medium\",\"investment_horizon\":\"1y\",\"interests\":[\"Technology\"],\"goal\":\"growth\"}"
```

Poll `GET /api/v1/analysis/<session_id>/status` until `completed`, then `GET /api/v1/analysis/<session_id>/results`.

---

## Tests (backend)

From the **`backend`** directory the test package resolves as **`app`**:

```cmd
cd backend
set PYTHONPATH=%CD%
python -m pytest -q
```

(PowerShell: `$env:PYTHONPATH=(Get-Location).Path`)

Coverage includes indicators, portfolio math, and authenticated API flows (with mocks).

---

## Without `GEMINI_API_KEY`

You still get **live market data** (subject to **yfinance** limits), **indicators**, **allocations**, **charts**, deterministic rationale fields, **auth**, and **daily snapshot** widgets. Gemini-heavy text falls back gracefully.

---

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| **401 on `/analyze`** | Register or login first; send `Authorization: Bearer …` |
| **Port already in use** | Change host port in the run command / `docker-compose.yml` |
| **Frontend cannot reach API** | Local: backend on `:8000`, Vite proxy. Docker: use `:3000` so nginx proxies `/api` |
| **`gemini_configured: false`** | Set `GEMINI_API_KEY`, restart backend |
| **SQLite “no such column” on very old DBs** | Current `init_db` upgrades schema in-place; if something is still wedged, stop backend, rename/delete `backend\data\app.db`, restart (data loss). |
| **Startup stays on “Waiting for application startup…”** | The first daily market snapshot runs in the **background** after DB init so the API can bind immediately; it may still be fetching Yahoo data via yfinance for a minute or two. |
| **Python 3.14 pip errors** | Use Python **3.12/3.13** or Docker |
| **`git commit` fails (identity)** | Configure `git config user.name` and `user.email` (globally or in repo) |

---

## Important disclaimers

- Outputs are **research and education only**, not investment, tax, or legal advice.
- “Expected return” and similar labels are **heuristic / momentum-style proxies**, not forecasts.
- Market data depends on **third-party sources** (e.g. yfinance); outages and delays are possible.

---

## License

See `LICENSE`.
