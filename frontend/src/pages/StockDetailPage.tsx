import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, TrendingUp, TrendingDown, BarChart3, PieChart, Zap, Activity, AlertCircle } from "lucide-react";
import { getTickerNews, getPriceHistory } from "../api";
import { useLivePrice } from "../hooks/useWebSocket";
import { StockPriceChart } from "../components/StockPriceChart";

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
    operatingMargins?: number;
    grossMargins?: number;
    totalCash?: number;
    totalDebt?: number;
    enterpriseValue?: number;
  };
}

interface NewsItem {
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  image?: string;
}

export function StockDetailPage() {
  const { ticker } = useParams<{ ticker: string }>();
  const navigate = useNavigate();
  const [stock, setStock] = useState<StockInfo | null>(null);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [priceHistory, setPriceHistory] = useState<{ date: string; close: number }[]>([]);
  
  // Real-time price updates
  const { price: livePrice, change, changePercent, isLive } = useLivePrice(ticker || "");

  useEffect(() => {
    // In a real app, you'd fetch stock data from an API
    // For now, we'll use localStorage or pass data via state
    const stockData = sessionStorage.getItem(`stock_${ticker}`);
    if (stockData) {
      setStock(JSON.parse(stockData));
    }
    
    // Fetch news for the stock
    const fetchNews = async () => {
      try {
        if (ticker) {
          const result = await getTickerNews(ticker);
          setNews(result.items || []);
        }
      } catch (err) {
        console.error("Failed to load news:", err);
        setNews([]);
      } finally {
        setLoading(false);
      }
    };
    
    // Fetch price history
    const fetchPriceHistory = async () => {
      try {
        if (ticker) {
          const result = await getPriceHistory(ticker, "1y");
          setPriceHistory(result.points || []);
        }
      } catch (err) {
        console.error("Failed to load price history:", err);
      }
    };
    
    fetchNews();
    fetchPriceHistory();
  }, [ticker]);

  if (!stock) {
    return (
      <div className="min-h-screen bg-slate-950 p-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 mb-8"
        >
          <ArrowLeft className="h-5 w-5" />
          Back
        </button>
        <div className="text-center text-slate-400">Loading stock data...</div>
      </div>
    );
  }

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

  // Use live price if available, otherwise use stored price
  const displayPrice = livePrice !== null ? livePrice : stock.current_price;
  const displayChange = livePrice !== null ? changePercent : stock.ytd_return_pct ?? 0;
  const isPositive = displayChange >= 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-indigo-400 hover:text-indigo-300 mb-6 transition"
        >
          <ArrowLeft className="h-5 w-5" />
          Back to Dashboard
        </button>

        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-4xl font-bold text-white mb-2">{stock.ticker}</h1>
            {stock.company_name && (
              <p className="text-lg text-slate-400">{stock.company_name}</p>
            )}
          </div>
          <div className="text-right">
            <div className="flex items-center gap-3 mb-2">
              <p className={`text-4xl font-bold transition-colors duration-300 ${
                isLive && change !== 0 
                  ? (change > 0 ? 'text-green-400' : 'text-red-400')
                  : 'text-white'
              }`}>
                {displayPrice ? `$${displayPrice.toFixed(2)}` : "N/A"}
              </p>
            </div>
            <p
              className={`text-2xl font-semibold ${
                isPositive ? "text-emerald-400" : "text-red-400"
              }`}
            >
              {isPositive ? "+" : ""}
              {displayChange.toFixed(2)}%
            </p>
            {isLive && change !== 0 && (
              <p className={`text-sm ${change > 0 ? "text-green-400" : "text-red-400"}`}>
                {change > 0 ? "+" : ""}{change.toFixed(2)} ({changePercent > 0 ? "+" : ""}{changePercent.toFixed(2)}%) today
              </p>
            )}
          </div>
        </div>

        {stock.info?.sector && (
          <div className="flex gap-2">
            <span className="inline-block rounded-full bg-indigo-500/20 px-4 py-2 text-sm font-semibold text-indigo-300 border border-indigo-500/30">
              {stock.info.sector}
            </span>
            {stock.info?.industry && (
              <span className="inline-block rounded-full bg-slate-700/50 px-4 py-2 text-sm font-semibold text-slate-300 border border-slate-600/30">
                {stock.info.industry}
              </span>
            )}
          </div>
        )}
      </motion.div>

      {/* Price Chart Section */}
      {priceHistory.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="mb-8 rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
        >
          <h2 className="text-xl font-bold text-white mb-6">Price History (1 Year)</h2>
          <StockPriceChart tickers={[ticker || ""]} defaultTicker={ticker || ""} />
        </motion.div>
      )}

      {/* Main Content Grid */}
      <div className="grid gap-8 lg:grid-cols-3">
        {/* Left Column - Detailed Metrics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Valuation Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
          >
            <div className="flex items-center gap-3 mb-6">
              <BarChart3 className="h-6 w-6 text-indigo-400" />
              <h2 className="text-xl font-bold text-white">Valuation Metrics</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Market Cap</p>
                <p className="text-2xl font-bold text-white">{formatNumber(stock.info?.marketCap)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Enterprise Value</p>
                <p className="text-2xl font-bold text-white">{formatNumber(stock.info?.enterpriseValue)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">P/E Ratio</p>
                <p className="text-2xl font-bold text-white">{stock.info?.trailingPE?.toFixed(2) ?? "N/A"}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Beta</p>
                <p className="text-2xl font-bold text-white">{stock.info?.beta?.toFixed(2) ?? "N/A"}</p>
              </div>
            </div>
          </motion.div>

          {/* Profitability Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
          >
            <div className="flex items-center gap-3 mb-6">
              <TrendingUp className="h-6 w-6 text-emerald-400" />
              <h2 className="text-xl font-bold text-white">Profitability & Margins</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Gross Margin</p>
                <p className="text-2xl font-bold text-emerald-400">{formatPercent(stock.info?.grossMargins)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Operating Margin</p>
                <p className="text-2xl font-bold text-emerald-400">{formatPercent(stock.info?.operatingMargins)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Profit Margin</p>
                <p className="text-2xl font-bold text-emerald-400">{formatPercent(stock.info?.profitMargins)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">ROE</p>
                <p className="text-2xl font-bold text-emerald-400">{formatPercent(stock.info?.returnOnEquity)}</p>
              </div>
            </div>
          </motion.div>

          {/* Growth Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
          >
            <div className="flex items-center gap-3 mb-6">
              <Zap className="h-6 w-6 text-yellow-400" />
              <h2 className="text-xl font-bold text-white">Growth Metrics</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Revenue Growth</p>
                <p className="text-2xl font-bold text-yellow-400">{formatPercent(stock.info?.revenueGrowth)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Earnings Growth</p>
                <p className="text-2xl font-bold text-yellow-400">{formatPercent(stock.info?.earningsGrowth)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Free Cash Flow</p>
                <p className="text-2xl font-bold text-yellow-400">{formatNumber(stock.info?.freeCashflow)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Dividend Yield</p>
                <p className="text-2xl font-bold text-yellow-400">{formatPercent(stock.info?.dividendYield)}</p>
              </div>
            </div>
          </motion.div>

          {/* Financial Health Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
          >
            <div className="flex items-center gap-3 mb-6">
              <PieChart className="h-6 w-6 text-purple-400" />
              <h2 className="text-xl font-bold text-white">Financial Health</h2>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Total Cash</p>
                <p className="text-2xl font-bold text-purple-400">{formatNumber(stock.info?.totalCash)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Total Debt</p>
                <p className="text-2xl font-bold text-purple-400">{formatNumber(stock.info?.totalDebt)}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Debt/Equity</p>
                <p className="text-2xl font-bold text-purple-400">{stock.info?.debtToEquity?.toFixed(2) ?? "N/A"}</p>
              </div>
              <div className="rounded-lg bg-slate-800/30 p-4 border border-slate-700/30">
                <p className="text-sm text-slate-400 mb-1">Current Ratio</p>
                <p className="text-2xl font-bold text-purple-400">{stock.info?.currentRatio?.toFixed(2) ?? "N/A"}</p>
              </div>
            </div>
          </motion.div>

          {/* 52-Week Range */}
          {stock.info?.fiftyTwoWeekLow && stock.info?.fiftyTwoWeekHigh && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
            >
              <h2 className="text-xl font-bold text-white mb-6">52-Week Price Range</h2>
              <div className="space-y-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-slate-400">Low: ${stock.info.fiftyTwoWeekLow.toFixed(2)}</span>
                  <span className="text-slate-400">High: ${stock.info.fiftyTwoWeekHigh.toFixed(2)}</span>
                </div>
                <div className="w-full bg-slate-700/30 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 via-indigo-500 to-emerald-500 h-full"
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
                  <span className="text-slate-400">Current: ${stock.current_price?.toFixed(2)}</span>
                  <span className="text-slate-400">
                    {(
                      (((stock.current_price ?? 0) - stock.info.fiftyTwoWeekLow) /
                        stock.info.fiftyTwoWeekLow) *
                      100
                    ).toFixed(1)}
                    % from low
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Right Column - News & Summary */}
        <div className="space-y-6">
          {/* Quick Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
          >
            <h2 className="text-lg font-bold text-white mb-4">Quick Stats</h2>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">YTD Return</span>
                <span
                  className={`font-bold ${
                    isPositive ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {isPositive ? "+" : ""}
                  {(stock.ytd_return_pct ?? 0).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Avg Volume</span>
                <span className="text-white font-semibold">
                  {stock.info?.averageVolume
                    ? `${(stock.info.averageVolume / 1e6).toFixed(1)}M`
                    : "N/A"}
                </span>
              </div>
            </div>
          </motion.div>

          {/* Recent News */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-6 backdrop-blur"
          >
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">Recent News ({news.length})</h2>
            </div>
            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900/50">
              {news.map((article, idx) => {
                const publishDate = new Date(article.published_at);
                const formattedDate = publishDate.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
                });

                return (
                  <a
                    key={idx}
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block rounded-lg border border-slate-700/30 bg-slate-800/20 p-3 hover:bg-slate-800/40 transition group"
                  >
                    <p className="text-sm font-semibold text-white group-hover:text-indigo-300 line-clamp-2 mb-2">
                      {article.title}
                    </p>
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{article.source}</span>
                      <span>{formattedDate}</span>
                    </div>
                  </a>
                );
              })}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
