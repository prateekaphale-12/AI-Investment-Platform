import { useEffect, useRef, useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { TrendingUp, TrendingDown, Loader } from "lucide-react";
import { getStocks } from "../api";

interface Stock {
  ticker: string;
  current_price?: number;
  ytd_return_pct: number;
  company_name?: string;
  info?: Record<string, unknown>;
}

interface InfiniteStocksListProps {
  category: "picks" | "gainers" | "losers";
  title: string;
  icon: React.ReactNode;
  colorClass: string;
  borderColorClass: string;
  hoverBorderClass: string;
  hoverShadowClass: string;
  isFixed?: boolean; // For top picks - no scroll
  maxHeight?: string; // Custom max height
}

export function InfiniteStocksList({
  category,
  title,
  icon,
  colorClass,
  borderColorClass,
  hoverBorderClass,
  hoverShadowClass,
  isFixed = false,
  maxHeight = "max-h-96",
}: InfiniteStocksListProps) {
  const navigate = useNavigate();
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [offset, setOffset] = useState(0);
  const observerTarget = useRef<HTMLDivElement>(null);

  // Load initial stocks
  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true);
      try {
        const result = await getStocks(category, 0, 10);
        setStocks(result.items);
        setOffset(10);
        setHasMore(result.total > 10);
      } catch (err) {
        console.error(`Failed to load ${category}:`, err);
      } finally {
        setLoading(false);
      }
    };

    loadInitial();
  }, [category]);

  // Load more stocks when scrolling (skip for fixed/picks)
  const loadMore = useCallback(async () => {
    if (loading || !hasMore || isFixed) return;

    setLoading(true);
    try {
      const result = await getStocks(category, offset, 10);
      if (result.items.length > 0) {
        setStocks((prev) => [...prev, ...result.items]);
        setOffset((prev) => prev + result.items.length);
        setHasMore(offset + result.items.length < result.total);
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error(`Failed to load more ${category}:`, err);
    } finally {
      setLoading(false);
    }
  }, [category, offset, loading, hasMore, isFixed]);

  // Intersection observer for infinite scroll (skip for fixed/picks)
  useEffect(() => {
    if (isFixed) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [loadMore, hasMore, loading, isFixed]);

  return (
    <>
      <motion.div
        whileHover={{ scale: 1.02, y: -4 }}
        transition={{ type: "spring", stiffness: 300 }}
        className={`group relative overflow-hidden rounded-2xl border ${borderColorClass} bg-gradient-to-br from-slate-900/40 to-slate-950/40 p-6 backdrop-blur-xl shadow-xl hover:shadow-2xl ${hoverShadowClass} hover:${hoverBorderClass} flex flex-col`}
        style={{ minHeight: isFixed ? "400px" : "auto" }}
      >
      <div className={`absolute right-0 top-0 h-32 w-32 ${colorClass}/10 blur-3xl group-hover:${colorClass}/20 transition-all duration-500`}></div>
      <div className="relative flex-1 flex flex-col">
        <div className="mb-5 flex items-center justify-between">
          <h3 className={`text-xs font-bold uppercase tracking-wider ${colorClass}`}>{title}</h3>
          <div className={`rounded-lg ${colorClass}/10 p-2`}>{icon}</div>
        </div>
        <div className={`space-y-3 flex-1 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900/50 hover:scrollbar-thumb-slate-600 max-h-[280px]`}>
          <AnimatePresence mode="popLayout">
            {stocks.map((stock, idx) => (
              <motion.div
                key={`${stock.ticker}-${idx}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: idx * 0.05 }}
                onClick={() => {
                  // Store stock data in sessionStorage for the detail page
                  sessionStorage.setItem(`stock_${stock.ticker}`, JSON.stringify(stock));
                  navigate(`/stock/${stock.ticker}`);
                }}
                className="rounded-lg bg-slate-800/20 p-3 hover:bg-slate-800/40 transition border border-slate-700/30 cursor-pointer"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex-1">
                    <span className="font-mono text-sm font-bold text-white">{stock.ticker}</span>
                    {stock.company_name && (
                      <p className="text-xs text-slate-400 mt-0.5">{stock.company_name}</p>
                    )}
                  </div>
                  <span
                    className={`font-mono text-sm font-semibold flex-shrink-0 ${
                      (stock.ytd_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                    }`}
                  >
                    {(stock.ytd_return_pct ?? 0) > 0 ? "+" : ""}
                    {(stock.ytd_return_pct ?? 0).toFixed(1)}%
                  </span>
                </div>
                {stock.current_price && (
                  <p className="text-xs text-slate-400">
                    Price: <span className="text-slate-200 font-semibold">${(stock.current_price as number).toFixed(2)}</span>
                  </p>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Loading indicator */}
          {loading && !isFixed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-center py-4"
            >
              <Loader className="h-5 w-5 animate-spin text-slate-400" />
            </motion.div>
          )}

          {/* Intersection observer target */}
          {!isFixed && <div ref={observerTarget} className="h-4" />}

          {/* End of list message */}
          {!hasMore && stocks.length > 0 && !isFixed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-4 text-xs text-slate-500"
            >
              No more stocks to load
            </motion.div>
          )}
        </div>
      </div>
      </motion.div>
    </>
  );
}
