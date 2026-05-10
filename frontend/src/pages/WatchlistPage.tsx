import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { listWatchlist, removeWatchlist } from "../api";

export function WatchlistPage() {
  const [items, setItems] = useState<{ id: string; ticker: string; ticker_name: string | null }[]>([]);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      const data = await listWatchlist();
      setItems(data.items);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function remove(t: string) {
    await removeWatchlist(t);
    await refresh();
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold text-white">Watchlist</h1>
        <Link
          to="/"
          className="rounded-lg bg-indigo-500 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-400"
        >
          Run new analysis
        </Link>
      </div>
      {loading ? (
        <p className="text-sm text-slate-400">Loading…</p>
      ) : items.length === 0 ? (
        <p className="text-sm text-slate-400">No saved tickers yet. Star a name from the results grid.</p>
      ) : (
        <ul className="space-y-3">
          {items.map((w) => (
            <li
              key={w.id}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-3"
            >
              <div>
                <p className="font-semibold text-white">{w.ticker}</p>
                {w.ticker_name ? <p className="text-xs text-slate-400">{w.ticker_name}</p> : null}
              </div>
              <button
                type="button"
                onClick={() => void remove(w.ticker)}
                className="text-xs text-rose-300 hover:text-rose-200"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
