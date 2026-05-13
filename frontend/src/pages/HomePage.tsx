import { useCallback, useEffect, useRef, useState } from "react";

import {
  getCapabilities,
  getDailySnapshot,
  getResults,
  getStatus,
  postAnalyze,
  type AnalyzePayload,
} from "../api";
import { AIReport } from "../components/AIReport";
import { AllocationPieChart } from "../components/AllocationPieChart";
import { LoadingIndicator } from "../components/LoadingIndicator";
import type { Allocation } from "../components/PortfolioResults";
import { PortfolioResults } from "../components/PortfolioResults";
import { QueryForm } from "../components/QueryForm";
import { StockPriceChart } from "../components/StockPriceChart";

export function HomePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [phase, setPhase] = useState<"idle" | "loading" | "done" | "error">("idle");
  const [statusDetail, setStatusDetail] = useState<string>("");
  const [results, setResults] = useState<{
    summary: Record<string, unknown> | null;
    portfolio: { allocations?: Allocation[] };
    report: string;
    status: string;
    errors?: string[];
  } | null>(null);
  const [geminiConfigured, setGeminiConfigured] = useState<boolean | null>(null);
  const [snapshot, setSnapshot] = useState<{
    picks: Array<{ ticker: string; ytd_return_pct: number }>;
    gainers: Array<{ ticker: string; ytd_return_pct: number }>;
    losers: Array<{ ticker: string; ytd_return_pct: number }>;
    metrics: { universe_count: number; avg_return_pct: number };
  } | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPoll(), [stopPoll]);
  useEffect(() => {
    let mounted = true;
    getCapabilities()
      .then((c) => {
        if (mounted) setGeminiConfigured(c.gemini_configured);
      })
      .catch(() => {
        if (mounted) setGeminiConfigured(null);
      });
    return () => {
      mounted = false;
    };
  }, []);
  useEffect(() => {
    getDailySnapshot().then((s) => setSnapshot(s)).catch(() => setSnapshot(null));
  }, []);

  async function handleAnalyze(payload: AnalyzePayload) {
    stopPoll();
    setPhase("loading");
    setResults(null);
    const { session_id } = await postAnalyze(payload);
    setSessionId(session_id);

    pollRef.current = setInterval(async () => {
      try {
        const s = await getStatus(session_id);
        setStatusDetail(
          s.current_agent ? `Step: ${s.current_agent.replace(/_/g, " ")}` : "Working…",
        );
        if (s.status === "failed") {
          stopPoll();
          setPhase("error");
          const r = await getResults(session_id);
          setResults({
            summary: r.summary ?? null,
            portfolio: r.portfolio ?? {},
            report: r.report ?? "",
            status: r.status,
            errors: r.errors ?? [],
          });
        }
        if (s.status === "completed") {
          stopPoll();
          const r = await getResults(session_id);
          setResults({
            summary: r.summary ?? null,
            portfolio: r.portfolio ?? {},
            report: r.report ?? "",
            status: r.status,
            errors: r.errors ?? [],
          });
          setPhase("done");
        }
      } catch {
        stopPoll();
        setPhase("error");
      }
    }, 2000);
  }

  const allocations: Allocation[] = results?.portfolio?.allocations ?? [];
  const chartData = allocations.map((a) => ({ name: a.ticker, value: a.allocation_pct }));
  const tickers = allocations.map((a) => a.ticker).filter(Boolean);
  const best = (results?.summary?.best_performer as string | undefined) ?? tickers[0];

  return (
    <div className="space-y-10">
      <section className="rounded-3xl border border-indigo-500/20 bg-gradient-to-br from-indigo-900/40 via-slate-900 to-slate-950 p-8 md:p-10">
        <p className="text-xs font-semibold uppercase tracking-widest text-indigo-200/80">
          Portfolio intelligence
        </p>
        <div className="mt-2 text-xs">
          {geminiConfigured === true ? (
            <span className="rounded bg-emerald-500/15 px-2 py-1 text-emerald-200">
              Gemini narrative: enabled
            </span>
          ) : geminiConfigured === false ? (
            <span className="rounded bg-amber-500/15 px-2 py-1 text-amber-200">
              Gemini narrative: not configured (fallback report mode)
            </span>
          ) : null}
        </div>
        <h1 className="mt-3 text-balance text-3xl font-semibold text-white md:text-4xl">
          AI investment research you can inspect — not a price oracle.
        </h1>
        <p className="mt-4 max-w-2xl text-sm text-slate-300 md:text-base">
          We orchestrate deterministic data pulls and technical math, then use Gemini strictly for readable narrative.
          Every number you see traces back to code, not improvised LLM math.
        </p>
        <p className="mt-4 max-w-2xl text-sm text-slate-300 md:text-base">
          Use the form below to run a new analysis. Your history is tied to your account.
        </p>
      </section>
      {snapshot ? (
        <section className="grid gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs">
            <p className="text-slate-400">Today's picks</p>
            {snapshot.picks.map((p) => (
              <p key={p.ticker} className="text-white">
                {p.ticker} ({p.ytd_return_pct}%)
              </p>
            ))}
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs">
            <p className="text-slate-400">Top highs</p>
            {snapshot.gainers.map((g) => (
              <p key={g.ticker} className="text-emerald-300">
                {g.ticker} ({g.ytd_return_pct}%)
              </p>
            ))}
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs">
            <p className="text-slate-400">Top lows</p>
            {snapshot.losers.map((l) => (
              <p key={l.ticker} className="text-rose-300">
                {l.ticker} ({l.ytd_return_pct}%)
              </p>
            ))}
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-xs">
            <p className="text-slate-400">Daily metrics</p>
            <p className="text-white">Universe: {snapshot.metrics.universe_count}</p>
            <p className="text-white">Avg return: {snapshot.metrics.avg_return_pct}%</p>
          </div>
        </section>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-5 lg:items-start">
        <div className="lg:col-span-2">
          <QueryForm onSubmit={(p) => void handleAnalyze(p)} disabled={phase === "loading"} />
        </div>
        <div className="space-y-4 lg:col-span-3">
          {phase === "loading" ? (
            <LoadingIndicator detail={statusDetail || "Polling analysis status…"} />
          ) : null}
          {phase === "error" ? (
            <p className="rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              Analysis failed or degraded. Expand cards below if partial data is present.
            </p>
          ) : null}

          {results && allocations.length ? (
            <>
              {results.summary ? (
                <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4 text-sm text-slate-300">
                  <p className="font-semibold text-white">Quick read</p>
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <div>
                      Portfolio budget ·{" "}
                      <span className="text-white">
                        ${Number(results.summary.total_budget ?? 0).toLocaleString()}
                      </span>
                    </div>
                    <div>
                      Heuristic blend (not forecast) ·{" "}
                      <span className="text-white">{String(results.summary.total_expected_return ?? "—")}%</span>
                    </div>
                    <div>
                      Diversification score ·{" "}
                      <span className="text-white">{String(results.summary.diversification_score ?? "—")}</span>
                    </div>
                    <div>
                      Standout ticker · <span className="text-white">{String(results.summary.best_performer ?? "—")}</span>
                    </div>
                  </div>
                </div>
              ) : null}
              {results.errors?.length ? (
                <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-xs text-amber-100">
                  Partial-data warnings: {results.errors.join(" | ")}
                </div>
              ) : null}

              <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
                <h2 className="mb-3 text-sm font-semibold text-white">Allocation mix</h2>
                <AllocationPieChart data={chartData} />
              </div>

              <PortfolioResults
                allocations={allocations}
                sessionId={sessionId}
                onWatchlistChange={() => undefined}
              />

              <StockPriceChart tickers={tickers} defaultTicker={best} />

              {results.report ? (
                <div>
                  <h2 className="mb-3 text-sm font-semibold text-white">AI research memo</h2>
                  <AIReport markdown={results.report} />
                </div>
              ) : null}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}
