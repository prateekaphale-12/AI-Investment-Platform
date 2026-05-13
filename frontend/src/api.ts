import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE ?? "";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export function getToken(): string | null {
  return localStorage.getItem("access_token");
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem("access_token", token);
  else localStorage.removeItem("access_token");
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type ApiUser = { id: string; email: string };

export type AnalyzePayload = {
  budget: number;
  risk_tolerance: "low" | "medium" | "high";
  investment_horizon: string;
  interests: string[];
  goal: "growth" | "income" | "balanced";
};

export async function postAnalyze(body: AnalyzePayload) {
  const { data } = await api.post<{ session_id: string; status: string }>("/api/v1/analyze", body);
  return data;
}

export async function getStatus(sessionId: string) {
  const { data } = await api.get<{
    session_id: string;
    status: string;
    current_agent: string | null;
    agents_completed: number;
    agents_total: number;
    errors: string[];
  }>(`/api/v1/analysis/${sessionId}/status`);
  return data;
}

export async function getResults(sessionId: string) {
  const { data } = await api.get(`/api/v1/analysis/${sessionId}/results`);
  return data;
}

export async function getPriceHistory(ticker: string, period: string) {
  const { data } = await api.get<{ points: { date: string; close: number }[] }>(
    `/api/v1/stocks/${ticker}/price`,
    { params: { period } },
  );
  return data;
}

export async function addWatchlist(sessionId: string | null, ticker: string, tickerName?: string) {
  await api.post("/api/v1/watchlist", { session_id: sessionId, ticker, ticker_name: tickerName });
}

export async function listWatchlist() {
  const { data } = await api.get<{ items: { id: string; ticker: string; ticker_name: string | null }[] }>(
    "/api/v1/watchlist",
  );
  return data;
}

export async function removeWatchlist(ticker: string) {
  await api.delete(`/api/v1/watchlist/${ticker}`);
}

export async function deleteWatchlistItem(id: string) {
  await api.delete(`/api/v1/watchlist/${id}`);
}

export async function getCapabilities() {
  const { data } = await api.get<{ gemini_configured: boolean; gemini_model: string }>(
    "/api/v1/capabilities",
  );
  return data;
}

export async function register(email: string, password: string) {
  const { data } = await api.post<{ access_token: string; user: { id: string; email: string } }>(
    "/api/v1/auth/register",
    { email, password },
  );
  return data;
}

export async function login(email: string, password: string) {
  const { data } = await api.post<{ access_token: string; user: { id: string; email: string } }>(
    "/api/v1/auth/login",
    { email, password },
  );
  return data;
}

export async function me() {
  const { data } = await api.get<{ id: string; email: string }>("/api/v1/auth/me");
  return data;
}

export async function getDailySnapshot() {
  const { data } = await api.get<{
    snapshot_date: string;
    picks: Array<{ ticker: string; current_price: number; ytd_return_pct: number }>;
    gainers: Array<{ ticker: string; ytd_return_pct: number }>;
    losers: Array<{ ticker: string; ytd_return_pct: number }>;
    metrics: { universe_count: number; avg_return_pct: number };
  }>("/api/v1/market/daily-snapshot");
  return data;
}

// LLM Provider Management
export async function getLLMProviders() {
  const { data } = await api.get<{ providers: Array<{ value: string; label: string; model: string }> }>("/api/v1/llm/providers");
  return data.providers;
}

export async function getLLMSettings() {
  const { data } = await api.get<{ provider: string; model: string; has_api_key: boolean }>("/api/v1/llm/settings");
  return data;
}

export async function saveLLMSettings(provider: string, apiKey: string) {
  const { data } = await api.post<{ message: string; provider: string }>("/api/v1/llm/settings", {
    provider,
    api_key: apiKey
  });
  return data;
}
