import { ExternalLink } from "lucide-react";

interface NewsItem {
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary?: string;
  image?: string;
  sentiment?: string;
}

interface TickerData {
  ticker: string;
  current_price?: number;
  ytd_return_pct: number;
}

interface SnapshotProps {
  picks: TickerData[];
  gainers: TickerData[];
  losers: TickerData[];
  metrics: { universe_count: number; avg_return_pct: number };
  topNews?: Record<string, NewsItem[]>;
  marketNews?: NewsItem[];
}

export function MarketSnapshot({
  picks,
  gainers,
  losers,
  metrics,
  topNews = {},
  marketNews = [],
}: SnapshotProps) {
  const formatDate = (dateStr: string) => {
    try {
      if (!dateStr) return "N/A";
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return "N/A";
      return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "2-digit" });
    } catch {
      return "N/A";
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment?.toUpperCase()) {
      case "POSITIVE":
        return "text-emerald-400";
      case "NEGATIVE":
        return "text-red-400";
      default:
        return "text-slate-400";
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Picks & Market Overview - Full Width Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Top Picks */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 hover:border-indigo-500/30 transition">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
            🚀 Top Picks
          </p>
          <div className="space-y-2">
            {picks.map((p) => (
              <div key={p.ticker} className="flex items-center justify-between text-sm">
                <span className="font-semibold text-white">{p.ticker}</span>
                <span
                  className={`font-medium ${
                    (p.ytd_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {(p.ytd_return_pct ?? 0) > 0 ? "+" : ""}
                  {(p.ytd_return_pct ?? 0).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Gainers */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 hover:border-emerald-500/30 transition">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-emerald-400">
            📈 Top Gainers
          </p>
          <div className="space-y-2">
            {gainers.slice(0, 4).map((g) => (
              <div key={g.ticker} className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{g.ticker}</span>
                <span className="font-medium text-emerald-400">+{(g.ytd_return_pct ?? 0).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Losers */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 hover:border-red-500/30 transition">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-red-400">
            📉 Top Losers
          </p>
          <div className="space-y-2">
            {losers.slice(0, 4).map((l) => (
              <div key={l.ticker} className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{l.ticker}</span>
                <span className="font-medium text-red-400">{(l.ytd_return_pct ?? 0).toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* Market Metrics */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 hover:border-slate-600/30 transition">
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-slate-400">
            📊 Market Metrics
          </p>
          <div className="space-y-3">
            <div>
              <p className="text-xs text-slate-500">Universe Size</p>
              <p className="text-lg font-semibold text-white">{metrics.universe_count}</p>
            </div>
            <div>
              <p className="text-xs text-slate-500">Avg Return</p>
              <p
                className={`text-lg font-semibold ${
                  (metrics.avg_return_pct ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {(metrics.avg_return_pct ?? 0) > 0 ? "+" : ""}
                {(metrics.avg_return_pct ?? 0).toFixed(2)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Latest News for Top Picks - Full Width */}
      {topNews && Object.keys(topNews).length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white">📰 Latest News - Top Picks</h3>
            <span className="text-xs text-slate-500">({Object.keys(topNews).length} stocks)</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Object.entries(topNews).map(([ticker, news]) => (
              <div key={ticker} className="space-y-2">
                <div className="flex items-center gap-2 rounded-lg bg-slate-800/50 px-3 py-2">
                  <span className="text-xs font-bold text-indigo-400">{ticker}</span>
                  <span className="text-xs text-slate-500">({news.length} articles)</span>
                </div>
                {news && news.length > 0 ? (
                  news.slice(0, 2).map((article, idx) => (
                    <a
                      key={idx}
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-lg border border-slate-700 bg-slate-800/30 p-3 hover:bg-slate-800/50 hover:border-indigo-500/50 transition duration-200"
                    >
                      <div className="flex items-start gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-white line-clamp-2 hover:text-indigo-300">
                            {article.title}
                          </p>
                          <div className="mt-2 space-y-1">
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-xs text-slate-400 font-medium">{article.source}</span>
                              <span className="text-xs text-slate-600">
                                {formatDate(article.published_at)}
                              </span>
                            </div>
                            {article.sentiment && (
                              <p className={`text-xs font-semibold ${getSentimentColor(article.sentiment)}`}>
                                {article.sentiment}
                              </p>
                            )}
                          </div>
                        </div>
                        <ExternalLink className="h-4 w-4 flex-shrink-0 text-slate-500 hover:text-indigo-400" />
                      </div>
                    </a>
                  ))
                ) : (
                  <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-3 text-xs text-slate-500">
                    No news available
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* General Market News - Full Width */}
      {marketNews && marketNews.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-white">🌍 Market News & Insights</h3>
            <span className="text-xs text-slate-500">({marketNews.length} articles)</span>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
            {marketNews.slice(0, 6).map((article, idx) => (
              <a
                key={idx}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex items-start gap-4 rounded-lg border border-slate-700 bg-gradient-to-r from-slate-800/40 to-slate-900/40 p-4 hover:border-indigo-500/50 hover:bg-slate-800/60 transition duration-200"
              >
                {article.image && (
                  <div className="flex-shrink-0">
                    <img
                      src={article.image}
                      alt=""
                      className="h-24 w-24 rounded-lg object-cover border border-slate-700 group-hover:border-indigo-500/50"
                      onError={(e) => {
                        e.currentTarget.style.display = "none";
                      }}
                    />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-white line-clamp-2 group-hover:text-indigo-300 transition">
                    {article.title}
                  </p>
                  {article.summary && (
                    <p className="mt-2 text-xs text-slate-400 line-clamp-2">
                      {article.summary}
                    </p>
                  )}
                  <div className="mt-3 flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-slate-500 bg-slate-800/50 px-2 py-1 rounded">
                      {article.source}
                    </span>
                    <span className="text-xs text-slate-600">
                      {formatDate(article.published_at)}
                    </span>
                  </div>
                </div>
                <ExternalLink className="h-5 w-5 flex-shrink-0 text-slate-500 group-hover:text-indigo-400 transition" />
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
