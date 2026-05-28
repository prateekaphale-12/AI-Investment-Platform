import { useCallback, useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Activity, DollarSign, ExternalLink, Wifi, WifiOff } from "lucide-react";

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
import { InfiniteStocksList } from "../components/InfiniteStocksList";
import { CategorizedNewsList } from "../components/CategorizedNewsList";
import { LiveTickerTape } from "../components/LiveTickerTape";
import { MarketSentimentMeter } from "../components/MarketSentimentMeter";
import { EventAlertToast } from "../components/EventAlertToast";
import { useWebSocket } from "../hooks/useWebSocket";

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
  const [aiConfigured, setAiConfigured] = useState<boolean | null>(null);
  const [snapshot, setSnapshot] = useState<{
    picks: Array<{ ticker: string; ytd_return_pct: number; current_price?: number; company_name?: string }>;
    gainers: Array<{ ticker: string; ytd_return_pct: number; current_price?: number; company_name?: string }>;
    losers: Array<{ ticker: string; ytd_return_pct: number; current_price?: number; company_name?: string }>;
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
  
  // WebSocket connection for real-time updates (disabled for now - not critical for initial load)
  const { isConnected, connectionStatus } = useWebSocket({ autoConnect: false });

  const stopPoll = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  useEffect(() => () => stopPoll(), [stopPoll]);
  useEffect(() => {
    let mounted = true;
    const checkCapabilities = () => {
      getCapabilities()
        .then((c) => {
          if (mounted) setAiConfigured(c.ai_configured as boolean);
        })
        .catch(() => {
          if (mounted) setAiConfigured(null);
        });
    };
    
    checkCapabilities();
    
    // Refresh capabilities every 5 seconds to detect when user saves AI config
    const interval = setInterval(checkCapabilities, 5000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
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
    <div className="space-y-8">
      {/* Event Alert Toasts */}
      <EventAlertToast />
      
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-2xl border border-indigo-500/20 bg-gradient-to-br from-indigo-950/30 via-slate-900/50 to-slate-950/30 backdrop-blur-xl shadow-2xl shadow-indigo-500/10"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-purple-500/5"></div>
        <div className="relative z-10 p-8">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-slate-100 to-slate-300 bg-clip-text text-transparent">
                  Portfolio Intelligence
                </h1>
                <AnimatePresence mode="wait">
                  {aiConfigured === false ? (
                    <motion.span
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="rounded-full bg-amber-500/15 px-4 py-1.5 text-xs font-semibold text-amber-300 border border-amber-500/30 shadow-lg shadow-amber-500/10"
                    >
                      ⚠ Configure AI
                    </motion.span>
                  ) : null}
                </AnimatePresence>
              </div>
              <p className="mt-3 max-w-3xl text-sm text-slate-400 leading-relaxed">
                Institutional-grade research powered by deterministic data and AI narrative synthesis.
              </p>
            </div>
            
            {/* WebSocket Connection Status - HIDDEN */}
          </div>
        </div>
      </motion.div>

      {/* Market Overview Dashboard */}
      {snapshotLoading ? (
        <SnapshotSkeleton />
      ) : snapshot ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="grid gap-6 md:grid-cols-2 xl:grid-cols-4"
        >
          {/* Top Picks Card - NO SCROLL (fixed 5 items) */}
          <InfiniteStocksList
            category="picks"
            title="Top Picks"
            icon={<TrendingUp className="h-5 w-5 text-indigo-400" />}
            colorClass="text-indigo-400"
            borderColorClass="border-slate-800/50"
            hoverBorderClass="border-indigo-500/30"
            hoverShadowClass="shadow-2xl"
            isFixed={true}
            maxHeight="auto"
          />

          {/* Top Gainers Card */}
          <InfiniteStocksList
            category="gainers"
            title="Top Gainers"
            icon={<TrendingUp className="h-5 w-5 text-emerald-400" />}
            colorClass="text-emerald-400"
            borderColorClass="border-slate-800/50"
            hoverBorderClass="border-emerald-500/30"
            hoverShadowClass="shadow-emerald-500/10"
          />

          {/* Top Losers Card */}
          <InfiniteStocksList
            category="losers"
            title="Top Losers"
            icon={<TrendingDown className="h-5 w-5 text-red-400" />}
            colorClass="text-red-400"
            borderColorClass="border-slate-800/50"
            hoverBorderClass="border-red-500/30"
            hoverShadowClass="shadow-red-500/10"
          />

          {/* Market Metrics Card */}
          <motion.div
            whileHover={{ scale: 1.02, y: -4 }}
            transition={{ type: "spring", stiffness: 300 }}
            className="group relative overflow-hidden rounded-2xl border border-slate-800/50 bg-gradient-to-br from-slate-900/40 to-slate-950/40 p-6 backdrop-blur-xl shadow-xl hover:shadow-2xl hover:shadow-slate-500/10 hover:border-slate-500/30 flex flex-col"
            style={{ minHeight: "auto" }}
          >
            <div className="absolute right-0 top-0 h-32 w-32 bg-slate-500/10 blur-3xl group-hover:bg-slate-500/20 transition-all duration-500"></div>
            <div className="relative flex-1 flex flex-col">
              <div className="mb-5 flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Market Metrics</h3>
                <div className="rounded-lg bg-slate-500/10 p-2">
                  <Activity className="h-5 w-5 text-slate-400" />
                </div>
              </div>
              <div className="space-y-3">
                {/* Universe Size */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1 }}
                  className="rounded-lg bg-slate-800/30 border border-slate-700/30 p-3"
                >
                  <p className="text-xs text-slate-500 mb-1">Universe Size</p>
                  <p className="font-mono text-lg font-bold text-white">{snapshot.metrics.universe_count}</p>
                </motion.div>

                {/* Average Return */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                  className="rounded-lg bg-slate-800/30 border border-slate-700/30 p-3"
                >
                  <p className="text-xs text-slate-500 mb-1">Avg Return (YTD)</p>
                  <p
                    className={`font-mono text-lg font-bold ${
                      (snapshot.metrics.avg_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {(snapshot.metrics.avg_return_pct ?? 0) > 0 ? "+" : ""}
                    {((snapshot.metrics.avg_return_pct ?? 0) || 0).toFixed(2)}%
                  </p>
                </motion.div>

                {/* Top Picks Count */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.3 }}
                  className="rounded-lg bg-slate-800/30 border border-slate-700/30 p-3"
                >
                  <p className="text-xs text-slate-500 mb-1">Top Picks</p>
                  <p className="font-mono text-lg font-bold text-indigo-400">{snapshot.picks.length}</p>
                </motion.div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      ) : null}

      {/* Real-time Market Sentiment Meter - REMOVED */}

      {/* Main Content Grid */}
      <div className="grid gap-8 xl:grid-cols-12">
        {/* Left Sidebar: Analysis Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.2 }}
          className="xl:col-span-4"
        >
          <div className="sticky top-24">
            <div className="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-8 backdrop-blur-xl shadow-2xl">
              <div className="mb-6">
                <h2 className="text-lg font-bold text-white">Configure Analysis</h2>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                  Set your preferences for AI-powered portfolio research and analysis
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
          className="space-y-8 xl:col-span-8"
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
              <CategorizedNewsList />
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  );
}
