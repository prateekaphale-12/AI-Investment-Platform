import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE ?? "";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

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

export async function getCapabilities() {
  const { data } = await api.get<{ gemini_configured: boolean; gemini_model: string }>(
    "/api/v1/capabilities",
  );
  return data;
}
