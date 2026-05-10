import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getPriceHistory } from "../api";

type Props = {
  tickers: string[];
  defaultTicker?: string;
};

export function StockPriceChart({ tickers, defaultTicker }: Props) {
  const [ticker, setTicker] = useState(defaultTicker ?? tickers[0] ?? "");
  const [range, setRange] = useState<"1mo" | "6mo" | "1y">("1y");
  const [points, setPoints] = useState<{ date: string; close: number }[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticker) return;
    let cancelled = false;
    setLoading(true);
    getPriceHistory(ticker, range)
      .then((d) => {
        if (!cancelled) setPoints(d.points ?? []);
      })
      .catch(() => {
        if (!cancelled) setPoints([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker, range]);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-white">Price history</h3>
        <div className="flex flex-wrap gap-2">
          <select
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-white"
          >
            {tickers.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <div className="flex gap-1">
            {(
              [
                ["1M", "1mo"],
                ["6M", "6mo"],
                ["1Y", "1y"],
              ] as const
            ).map(([label, key]) => (
              <button
                key={key}
                type="button"
                onClick={() => setRange(key)}
                className={
                  range === key
                    ? "rounded-md bg-indigo-500/20 px-2 py-1 text-xs font-medium text-indigo-200"
                    : "rounded-md px-2 py-1 text-xs text-slate-400 hover:text-white"
                }
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
      {loading ? (
        <p className="text-sm text-slate-500">Loading chart…</p>
      ) : (
        <div className="h-64 w-full">
          <ResponsiveContainer>
            <LineChart data={points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="date" hide />
              <YAxis domain={["auto", "auto"]} stroke="#64748b" fontSize={11} />
              <Tooltip
                contentStyle={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 8 }}
                labelStyle={{ color: "#e2e8f0" }}
              />
              <Line type="monotone" dataKey="close" stroke="#818cf8" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
