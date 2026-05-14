import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Activity, DollarSign, ExternalLink } from "lucide-react";

import {
  downloadAnalysisPDF,
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
import { SnapshotSkeleton } from "../components/SnapshotSkeleton";
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
    top_news?: Record<string, Array<{
      title: string;
      url: string;
      source: string;
      published_at: string;
      summary?: string;
      image?: string;
      sentiment?: string;
    }>>;
    market_news?: Array<{
      title: string;
      url: string;
      source: string;
      published_at: string;
      summary?: string;
      image?: string;
    }>;
  } | null>(null);
  const [snapshotLoading, setSnapshotLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
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
    setSnapshotLoading(true);
    getDailySnapshot()
      .then((s) => {
        setSnapshot(s);
        setSnapshotLoading(false);
      })
      .catch(() => {
        setSnapshot(null);
        setSnapshotLoading(false);
      });

    const refreshInterval = setInterval(() => {
      getDailySnapshot()
        .then((s) => setSnapshot(s))
        .catch(() => setSnapshot(null));
    }, 30 * 60 * 1000);

    return () => clearInterval(refreshInterval);
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

  async function handleDownloadPDF() {
    if (!sessionId) return;
    try {
      setDownloading(true);
      const blob = await downloadAnalysisPDF(sessionId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `analysis-${sessionId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download PDF");
      console.error(err);
    } finally {
      setDownloading(false);
    }
  }

  // Flatten all news for ticker
  const allNews = snapshot?.top_news ? Object.entries(snapshot.top_news).flatMap(([ticker, articles]) =>
    articles.map(article => ({ ...article, ticker }))
  ) : [];

  return (
    <div className="space-y-6">
      {/* Hero Section with News Ticker */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/50 via-slate-900/80 to-slate-950"
      >
        <div className="relative z-10 p-6 md:p-8">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-white md:text-3xl">
                  Portfolio Intelligence
                </h1>
                <AnimatePresence mode="wait">
                  {geminiConfigured === true ? (
                    <motion.span
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="rounded-full bg-emerald-500/15 px-3 py-1 text-xs font-medium text-emerald-300 border border-emerald-500/30"
                    >
                      ✓ AI Enabled
                    </motion.span>
                  ) : geminiConfigured === false ? (
                    <motion.span
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="rounded-full bg-amber-500/15 px-3 py-1 text-xs font-medium text-amber-300 border border-amber-500/30"
                    >
                      ⚠ Fallback Mode
                    </motion.span>
                  ) : null}
                </AnimatePresence>
              </div>
              <p className="mt-2 max-w-2xl text-sm text-slate-300">
                Institutional-grade research powered by deterministic data and AI narrative synthesis.
              </p>
            </div>
          </div>
        </div>

        {/* News Ticker */}
        {allNews.length > 0 && (
          <div className="relative border-t border-indigo-500/10 bg-slate-950/50 backdrop-blur-sm overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-2">
              <Activity className="h-4 w-4 text-indigo-400 flex-shrink-0" />
              <div className="flex-1 overflow-hidden">
                <motion.div
                  className="flex gap-8"
                  animate={{ x: [0, -1000] }}
                  transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                >
                  {[...allNews, ...allNews].map((article, idx) => (
                    <a
                      key={idx}
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-2 whitespace-nowrap text-xs text-slate-400 hover:text-indigo-300 transition"
                    >
                      <span className="font-mono font-bold text-indigo-400">{article.ticker}</span>
                      <span>•</span>
                      <span>{article.title}</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  ))}
                </motion.div>
              </div>
            </div>
          </div>
        )}

        <div className="absolute right-0 top-0 h-full w-1/3 bg-gradient-to-l from-indigo-500/10 to-transparent"></div>
      </motion.div>

      {/* Market Overview Dashboard */}
      {snapshotLoading ? (
        <SnapshotSkeleton />
      ) : snapshot ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
        >
          {/* Top Picks Card */}
          <motion.div
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="group relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/60 to-slate-950/60 p-5 backdrop-blur"
          >
            <div className="absolute right-0 top-0 h-20 w-20 bg-indigo-500/5 blur-2xl"></div>
            <div className="relative">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Top Picks</h3>
                <TrendingUp className="h-5 w-5 text-indigo-400" />
              </div>
              <div className="space-y-2.5">
                {snapshot.picks.map((p, idx) => (
                  <motion.div
                    key={p.ticker}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="flex items-center justify-between"
                  >
                    <span className="font-mono text-sm font-bold text-white">{p.ticker}</span>
                    <span
                      className={`font-mono text-sm font-semibold ${
                        (p.ytd_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {(p.ytd_return_pct ?? 0) > 0 ? "+" : ""}
                      {(p.ytd_return_pct ?? 0).toFixed(1)}%
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Top Gainers Card */}
          <motion.div
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="group relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/60 to-slate-950/60 p-5 backdrop-blur"
          >
            <div className="absolute right-0 top-0 h-20 w-20 bg-emerald-500/5 blur-2xl"></div>
            <div className="relative">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-400">Top Gainers</h3>
                <TrendingUp className="h-5 w-5 text-emerald-400" />
              </div>
              <div className="space-y-2.5">
                {snapshot.gainers.slice(0, 4).map((g, idx) => (
                  <motion.div
                    key={g.ticker}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="flex items-center justify-between"
                  >
                    <span className="font-mono text-sm text-slate-300">{g.ticker}</span>
                    <span className="font-mono text-sm font-semibold text-emerald-400">
                      +{(g.ytd_return_pct ?? 0).toFixed(1)}%
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Top Losers Card */}
          <motion.div
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="group relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/60 to-slate-950/60 p-5 backdrop-blur"
          >
            <div className="absolute right-0 top-0 h-20 w-20 bg-red-500/5 blur-2xl"></div>
            <div className="relative">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-red-400">Top Losers</h3>
                <TrendingDown className="h-5 w-5 text-red-400" />
              </div>
              <div className="space-y-2.5">
                {snapshot.losers.slice(0, 4).map((l, idx) => (
                  <motion.div
                    key={l.ticker}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="flex items-center justify-between"
                  >
                    <span className="font-mono text-sm text-slate-300">{l.ticker}</span>
                    <span className="font-mono text-sm font-semibold text-red-400">
                      {(l.ytd_return_pct ?? 0).toFixed(1)}%
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Market Metrics Card */}
          <motion.div
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="group relative overflow-hidden rounded-xl border border-slate-800 bg-gradient-to-br from-slate-900/60 to-slate-950/60 p-5 backdrop-blur"
          >
            <div className="absolute right-0 top-0 h-20 w-20 bg-slate-500/5 blur-2xl"></div>
            <div className="relative">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Market Metrics</h3>
                <Activity className="h-5 w-5 text-slate-400" />
              </div>
              <div className="space-y-4">
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  <p className="text-xs text-slate-500">Universe Size</p>
                  <p className="mt-1 font-mono text-2xl font-bold text-white">{snapshot.metrics.universe_count}</p>
                </motion.div>
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                >
                  <p className="text-xs text-slate-500">Average Return</p>
                  <p
                    className={`mt-1 font-mono text-2xl font-bold ${
                      (snapshot.metrics.avg_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {(snapshot.metrics.avg_return_pct ?? 0) > 0 ? "+" : ""}
                    {(snapshot.metrics.avg_return_pct ?? 0).toFixed(2)}%
                  </p>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      ) : null}

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left Sidebar: Analysis Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-4"
        >
          <div className="sticky top-6">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur">
              <div className="mb-5">
                <h2 className="text-base font-bold text-white">Configure Analysis</h2>
                <p className="mt-1 text-xs text-slate-400">
                  Set your preferences for AI-powered portfolio research
                </p>
              </div>
              <QueryForm onSubmit={(p) => void handleAnalyze(p)} disabled={phase === "loading"} />
            </div>
          </div>
        </motion.div>

        {/* Right Content: Results or Market News */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-6 lg:col-span-8"
        >
          {/* Loading State */}
          <AnimatePresence>
            {phase === "loading" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="rounded-xl border border-indigo-500/30 bg-indigo-950/20 p-6"
              >
                <LoadingIndicator detail={statusDetail || "Analyzing market data…"} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Error State */}
          <AnimatePresence>
            {phase === "error" && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="rounded-xl border border-rose-500/40 bg-rose-950/20 p-4"
              >
                <p className="text-sm text-rose-200">
                  ⚠️ Analysis encountered issues. Partial results may be available below.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Results Display */}
          <AnimatePresence mode="wait">
            {results && allocations.length ? (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* Quick Summary */}
                {results.summary && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur"
                  >
                    <h3 className="mb-4 flex items-center gap-2 text-sm font-bold text-white">
                      <DollarSign className="h-4 w-4 text-emerald-400" />
                      Portfolio Summary
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        className="rounded-lg bg-slate-950/50 p-4"
                      >
                        <p className="text-xs text-slate-500">Total Budget</p>
                        <p className="mt-1 font-mono text-xl font-bold text-white">
                          ${Number(results.summary.total_budget ?? 0).toLocaleString()}
                        </p>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        className="rounded-lg bg-slate-950/50 p-4"
                      >
                        <p className="text-xs text-slate-500">Expected Return</p>
                        <p className="mt-1 font-mono text-xl font-bold text-emerald-400">
                          {String(results.summary.total_expected_return ?? "—")}%
                        </p>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        className="rounded-lg bg-slate-950/50 p-4"
                      >
                        <p className="text-xs text-slate-500">Diversification</p>
                        <p className="mt-1 font-mono text-xl font-bold text-indigo-400">
                          {String(results.summary.diversification_score ?? "—")}
                        </p>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.02 }}
                        className="rounded-lg bg-slate-950/50 p-4"
                      >
                        <p className="text-xs text-slate-500">Best Performer</p>
                        <p className="mt-1 font-mono text-xl font-bold text-white">
                          {String(results.summary.best_performer ?? "—")}
                        </p>
                      </motion.div>
                    </div>
                  </motion.div>
                )}

                {/* Warnings */}
                {results.errors?.length ? (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="rounded-xl border border-amber-500/30 bg-amber-950/20 p-4"
                  >
                    <p className="text-xs text-amber-200">
                      ⚠️ {results.errors.join(" • ")}
                    </p>
                  </motion.div>
                ) : null}

                {/* Allocation Chart */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.1 }}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur"
                >
                  <h3 className="mb-4 text-sm font-bold text-white">Asset Allocation</h3>
                  <AllocationPieChart data={chartData} />
                </motion.div>

                {/* Portfolio Details */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                >
                  <PortfolioResults
                    allocations={allocations}
                    sessionId={sessionId}
                    onWatchlistChange={() => undefined}
                  />
                </motion.div>

                {/* Price Chart */}
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <StockPriceChart tickers={tickers} defaultTicker={best} />
                </motion.div>

                {/* AI Report */}
                {results.report && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur"
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-sm font-bold text-white">AI Research Memo</h3>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleDownloadPDF}
                        disabled={downloading}
                        className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        <span>{downloading ? "Downloading..." : "📥 Download PDF"}</span>
                      </motion.button>
                    </div>
                    <AIReport markdown={results.report} />
                  </motion.div>
                )}
              </motion.div>
            ) : (
              /* Market News When No Results */
              snapshot?.market_news && snapshot.market_news.length > 0 && (
                <motion.div
                  key="market-news"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur"
                >
                  <h3 className="mb-5 text-sm font-bold text-white">🌍 Market News & Insights</h3>
                  <div className="space-y-4">
                    {snapshot.market_news.slice(0, 6).map((article, idx) => (
                      <motion.a
                        key={idx}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        whileHover={{ scale: 1.02, x: 4 }}
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="group block rounded-lg border border-slate-800 bg-slate-950/50 p-4 transition hover:border-indigo-500/50 hover:bg-slate-900/50"
                      >
                        <div className="flex gap-4">
                          {article.image && (
                            <div className="flex-shrink-0">
                              <img
                                src={article.image}
                                alt=""
                                className="h-20 w-20 rounded-lg border border-slate-800 object-cover transition group-hover:border-indigo-500/50"
                                onError={(e) => {
                                  e.currentTarget.style.display = "none";
                                }}
                              />
                            </div>
                          )}
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-white line-clamp-2 group-hover:text-indigo-300 transition">
                              {article.title}
                            </h4>
                            {article.summary && (
                              <p className="mt-2 text-xs text-slate-400 line-clamp-2">
                                {article.summary}
                              </p>
                            )}
                            <div className="mt-3 flex items-center gap-3">
                              <span className="rounded bg-slate-800/50 px-2 py-1 text-xs font-medium text-slate-400">
                                {article.source}
                              </span>
                              <span className="text-xs text-slate-600">
                                {new Date(article.published_at).toLocaleDateString("en-US", {
                                  month: "short",
                                  day: "numeric",
                                })}
                              </span>
                            </div>
                          </div>
                        </div>
                      </motion.a>
                    ))}
                  </div>
                </motion.div>
              )
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
