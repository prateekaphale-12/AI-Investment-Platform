import { motion, AnimatePresence } from "framer-motion";
import { X, TrendingUp, TrendingDown, BarChart3, PieChart, Zap } from "lucide-react";
import { useEffect, useState } from "react";

interface StockInfo {
  ticker: string;
  company_name?: string;
  current_price?: number;
  ytd_return_pct: number;
  info?: {
    marketCap?: number;
    trailingPE?: number;
    beta?: number;
    profitMargins?: number;
    returnOnEquity?: number;
    debtToEquity?: number;
    revenueGrowth?: number;
    earningsGrowth?: number;
    freeCashflow?: number;
    currentRatio?: number;
    industry?: string;
    sector?: string;
    fiftyTwoWeekHigh?: number;
    fiftyTwoWeekLow?: number;
    averageVolume?: number;
    dividendYield?: number;
  };
}

interface StockDetailsModalProps {
  stock: StockInfo | null;
  isOpen: boolean;
  onClose: () => void;
}

export function StockDetailsModal({ stock, isOpen, onClose }: StockDetailsModalProps) {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  if (!stock) return null;

  const formatNumber = (num: number | undefined, decimals = 2) => {
    if (num === undefined || num === null) return "N/A";
    if (Math.abs(num) >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
    if (Math.abs(num) >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
    if (Math.abs(num) >= 1e3) return `$${(num / 1e3).toFixed(1)}K`;
    return `$${num.toFixed(decimals)}`;
  };

  const formatPercent = (num: number | undefined) => {
    if (num === undefined || num === null) return "N/A";
    return `${(num * 100).toFixed(2)}%`;
  };

  const isPositive = (stock.ytd_return_pct ?? 0) >= 0;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-slate-700 bg-gradient-to-br from-slate-900 to-slate-950 p-8 shadow-2xl max-h-[90vh] overflow-y-auto"
          >
            {/* Close Button */}
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={onClose}
              className="absolute right-4 top-4 rounded-lg bg-slate-800/50 p-2 hover:bg-slate-700 transition"
            >
              <X className="h-5 w-5 text-slate-400" />
            </motion.button>

            {/* Header */}
            <div className="mb-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-3xl font-bold text-white">{stock.ticker}</h2>
                  {stock.company_name && (
                    <p className="text-sm text-slate-400 mt-1">{stock.company_name}</p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-white">
                    {stock.current_price ? `$${stock.current_price.toFixed(2)}` : "N/A"}
                  </p>
                  <p
                    className={`text-lg font-semibold ${
                      isPositive ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {isPositive ? "+" : ""}
                    {(stock.ytd_return_pct ?? 0).toFixed(2)}%
                  </p>
                </div>
              </div>

              {stock.info?.sector && (
                <div className="flex gap-2">
                  <span className="inline-block rounded-full bg-indigo-500/20 px-3 py-1 text-xs font-semibold text-indigo-300 border border-indigo-500/30">
                    {stock.info.sector}
                  </span>
                  {stock.info?.industry && (
                    <span className="inline-block rounded-full bg-slate-700/50 px-3 py-1 text-xs font-semibold text-slate-300 border border-slate-600/30">
                      {stock.info.industry}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Key Metrics Grid */}
            <div className="grid gap-4 md:grid-cols-2 mb-6">
              {/* Valuation */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="h-4 w-4 text-indigo-400" />
                  <h3 className="text-sm font-semibold text-white">Valuation</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Market Cap</span>
                    <span className="text-white font-medium">{formatNumber(stock.info?.marketCap)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">P/E Ratio</span>
                    <span className="text-white font-medium">{stock.info?.trailingPE?.toFixed(2) ?? "N/A"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Beta</span>
                    <span className="text-white font-medium">{stock.info?.beta?.toFixed(2) ?? "N/A"}</span>
                  </div>
                </div>
              </motion.div>

              {/* Profitability */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="h-4 w-4 text-emerald-400" />
                  <h3 className="text-sm font-semibold text-white">Profitability</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Profit Margin</span>
                    <span className="text-white font-medium">{formatPercent(stock.info?.profitMargins)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">ROE</span>
                    <span className="text-white font-medium">{formatPercent(stock.info?.returnOnEquity)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Free Cash Flow</span>
                    <span className="text-white font-medium">{formatNumber(stock.info?.freeCashflow)}</span>
                  </div>
                </div>
              </motion.div>

              {/* Growth */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="h-4 w-4 text-yellow-400" />
                  <h3 className="text-sm font-semibold text-white">Growth</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Revenue Growth</span>
                    <span className="text-white font-medium">{formatPercent(stock.info?.revenueGrowth)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Earnings Growth</span>
                    <span className="text-white font-medium">{formatPercent(stock.info?.earningsGrowth)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Dividend Yield</span>
                    <span className="text-white font-medium">{formatPercent(stock.info?.dividendYield)}</span>
                  </div>
                </div>
              </motion.div>

              {/* Financial Health */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4"
              >
                <div className="flex items-center gap-2 mb-3">
                  <PieChart className="h-4 w-4 text-purple-400" />
                  <h3 className="text-sm font-semibold text-white">Financial Health</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Debt/Equity</span>
                    <span className="text-white font-medium">{stock.info?.debtToEquity?.toFixed(2) ?? "N/A"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Current Ratio</span>
                    <span className="text-white font-medium">{stock.info?.currentRatio?.toFixed(2) ?? "N/A"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">52W High</span>
                    <span className="text-white font-medium">${stock.info?.fiftyTwoWeekHigh?.toFixed(2) ?? "N/A"}</span>
                  </div>
                </div>
              </motion.div>
            </div>

            {/* 52 Week Range */}
            {stock.info?.fiftyTwoWeekLow && stock.info?.fiftyTwoWeekHigh && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="rounded-lg border border-slate-700/50 bg-slate-800/30 p-4 mb-6"
              >
                <h3 className="text-sm font-semibold text-white mb-3">52-Week Range</h3>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Low</span>
                    <span className="text-white font-medium">${stock.info.fiftyTwoWeekLow.toFixed(2)}</span>
                  </div>
                  <div className="w-full bg-slate-700/30 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-emerald-500 to-indigo-500 h-full"
                      style={{
                        width: `${
                          ((stock.current_price ?? 0) - stock.info.fiftyTwoWeekLow) /
                          (stock.info.fiftyTwoWeekHigh - stock.info.fiftyTwoWeekLow) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">High</span>
                    <span className="text-white font-medium">${stock.info.fiftyTwoWeekHigh.toFixed(2)}</span>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Close Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onClose}
              className="w-full rounded-lg bg-indigo-600 py-3 font-semibold text-white hover:bg-indigo-500 transition"
            >
              Close
            </motion.button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
