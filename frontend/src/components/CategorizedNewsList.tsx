import { useEffect, useRef, useCallback, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ExternalLink, Loader, Zap } from "lucide-react";
import { getNews } from "../api";

interface NewsItem {
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  image?: string;
  category?: string;
  sentiment?: string;
  sentiment_score?: number;
  dedupe_hash?: string;
}

interface NewsResponse {
  category: string;
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  items: NewsItem[];
  cached: boolean;
  freshness?: {
    age_seconds: number;
    ttl_remaining: number;
    cached_at: string;
  };
}

const NEWS_CATEGORIES = [
  { id: "general", label: "General" },
  { id: "finance", label: "Finance" },
  { id: "it", label: "IT & Tech" },
  { id: "healthcare", label: "Healthcare" },
  { id: "energy", label: "Energy" },
  { id: "real_estate", label: "Real Estate" },
];

const SENTIMENT_COLORS = {
  POSITIVE: "text-green-400 bg-green-400/10",
  NEGATIVE: "text-red-400 bg-red-400/10",
  NEUTRAL: "text-slate-400 bg-slate-400/10",
};

const SENTIMENT_LABELS = {
  POSITIVE: "📈 Positive",
  NEGATIVE: "📉 Negative",
  NEUTRAL: "➡️ Neutral",
};

export function CategorizedNewsList() {
  const [selectedCategory, setSelectedCategory] = useState("general");
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [freshness, setFreshness] = useState<any>(null);
  const observerTarget = useRef<HTMLDivElement>(null);

  // Load initial news
  useEffect(() => {
    const loadInitial = async () => {
      setLoading(true);
      setNews([]);
      setCurrentPage(1);
      try {
        const result = (await getNews(selectedCategory, 1)) as NewsResponse;
        setNews(result.items);
        setTotalPages(result.total_pages);
        setFreshness(result.freshness);
        setCurrentPage(1);
      } catch (err) {
        console.error("Failed to load news:", err);
      } finally {
        setLoading(false);
      }
    };

    loadInitial();
  }, [selectedCategory]);

  // Load more news when scrolling
  const loadMore = useCallback(async () => {
    if (loading || currentPage >= totalPages) return;

    setLoading(true);
    try {
      const nextPage = currentPage + 1;
      const result = (await getNews(selectedCategory, nextPage)) as NewsResponse;
      if (result.items.length > 0) {
        setNews((prev) => [...prev, ...result.items]);
        setCurrentPage(nextPage);
        setFreshness(result.freshness);
      }
    } catch (err) {
      console.error("Failed to load more news:", err);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, currentPage, totalPages, loading]);

  // Intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && currentPage < totalPages && !loading) {
          loadMore();
        }
      },
      { threshold: 0.1 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [loadMore, currentPage, totalPages, loading]);

  const formatFreshnessTime = (seconds: number) => {
    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur"
    >
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-bold text-white">🌍 Market News & Insights</h3>
        {freshness && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Zap className="h-3 w-3 text-yellow-400" />
            <span>Updated {formatFreshnessTime(freshness.age_seconds)}</span>
          </div>
        )}
      </div>

      {/* Category Filter Tabs */}
      <div className="mb-6 flex flex-wrap gap-2">
        {NEWS_CATEGORIES.map((cat) => (
          <motion.button
            key={cat.id}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setSelectedCategory(cat.id)}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition ${
              selectedCategory === cat.id
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/50"
                : "bg-slate-800/50 text-slate-300 hover:bg-slate-800 border border-slate-700/50"
            }`}
          >
            {cat.label}
          </motion.button>
        ))}
      </div>

      {/* News List with Infinite Scroll */}
      <div className="space-y-3 max-h-[1000px] overflow-y-auto pr-3 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900/50 hover:scrollbar-thumb-slate-600">
        <AnimatePresence mode="popLayout">
          {news.map((article, idx) => {
            const publishDate = new Date(article.published_at);
            const formattedDate = publishDate.toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
            const formattedTime = publishDate.toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            });

            const sentimentColor = SENTIMENT_COLORS[article.sentiment as keyof typeof SENTIMENT_COLORS] || SENTIMENT_COLORS.NEUTRAL;
            const sentimentLabel = SENTIMENT_LABELS[article.sentiment as keyof typeof SENTIMENT_LABELS] || SENTIMENT_LABELS.NEUTRAL;

            return (
              <motion.a
                key={`${article.dedupe_hash || article.url}-${idx}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: idx * 0.05 }}
                whileHover={{ scale: 1.01 }}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group block rounded-lg border border-slate-700/30 bg-slate-800/20 p-4 hover:bg-slate-800/40 hover:border-indigo-500/30 transition"
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    {/* Title */}
                    <h4 className="text-sm font-semibold text-white group-hover:text-indigo-300 transition line-clamp-2 mb-2">
                      {article.title}
                    </h4>
                    
                    {/* Summary */}
                    {article.summary && (
                      <p className="text-xs text-slate-400 line-clamp-2 mb-3">{article.summary}</p>
                    )}
                    
                    {/* Badges and Footer */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Sentiment Badge */}
                        {article.sentiment && (
                          <span className={`text-xs font-medium px-2 py-1 rounded ${sentimentColor}`}>
                            {sentimentLabel}
                          </span>
                        )}
                        
                        {/* Source Badge */}
                        <span className="text-xs text-slate-500 font-medium bg-slate-800/50 px-2 py-1 rounded truncate">
                          {article.source}
                        </span>
                        
                        {/* Date */}
                        <span className="text-xs text-slate-500 whitespace-nowrap">
                          {formattedDate} {formattedTime}
                        </span>
                      </div>
                      <ExternalLink className="h-3.5 w-3.5 text-slate-400 group-hover:text-indigo-400 transition flex-shrink-0" />
                    </div>
                  </div>
                </div>
              </motion.a>
            );
          })}
        </AnimatePresence>

        {/* Loading indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-center py-4"
          >
            <Loader className="h-5 w-5 animate-spin text-slate-400" />
          </motion.div>
        )}

        {/* Intersection observer target */}
        <div ref={observerTarget} className="h-4" />

        {/* End of list message */}
        {currentPage >= totalPages && news.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-4 text-xs text-slate-500"
          >
            No more news to load
          </motion.div>
        )}

        {/* Empty state */}
        {!loading && news.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12 text-sm text-slate-400"
          >
            <div className="mb-3 text-3xl">📰</div>
            <p className="font-medium">No news available</p>
            <p className="text-xs mt-1">Try another category or check back later</p>
          </motion.div>
        )}
      </div>

      {/* Pagination Info */}
      {totalPages > 1 && (
        <div className="mt-4 text-center text-xs text-slate-500">
          Page {currentPage} of {totalPages}
        </div>
      )}
    </motion.div>
  );
}

