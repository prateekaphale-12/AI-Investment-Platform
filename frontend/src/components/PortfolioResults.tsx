import { useState } from "react";

import { addWatchlist } from "../api";
import { WhyThisStock, type Rationale } from "./WhyThisStock";

export type Allocation = {
  ticker: string;
  allocation_pct: number;
  amount: number;
  expected_return: number;
  risk_score: number;
  rationale?: Rationale;
};

type Props = {
  allocations: Allocation[];
  sessionId: string | null;
  onWatchlistChange?: () => void;
};

export function PortfolioResults({ allocations, sessionId, onWatchlistChange }: Props) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {allocations.map((a) => (
        <div
          key={a.ticker}
          className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 shadow-lg shadow-slate-950/30"
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="text-lg font-bold text-white">{a.ticker}</p>
              <p className="text-xs text-slate-400">
                Alloc {a.allocation_pct}% · ${a.amount.toLocaleString()} · Heuristic return proxy{" "}
                {a.expected_return}%
              </p>
              <p className="mt-1 text-xs text-slate-500">Risk score (heuristic): {a.risk_score}</p>
            </div>
            <WatchlistButton
              sessionId={sessionId}
              ticker={a.ticker}
              onChange={onWatchlistChange}
            />
          </div>
          {a.rationale ? <WhyThisStock ticker={a.ticker} rationale={a.rationale} /> : null}
        </div>
      ))}
    </div>
  );
}

function WatchlistButton({
  sessionId,
  ticker,
  onChange,
}: {
  sessionId: string | null;
  ticker: string;
  onChange?: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  async function add() {
    setBusy(true);
    setMsg(null);
    try {
      await addWatchlist(sessionId, ticker);
      setMsg("Saved");
      onChange?.();
    } catch {
      setMsg("Error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      type="button"
      onClick={() => void add()}
      disabled={busy}
      className="shrink-0 rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-2 py-1 text-xs font-medium text-indigo-200 hover:bg-indigo-500/20 disabled:opacity-50"
    >
      {busy ? "…" : msg ?? "★ Watchlist"}
    </button>
  );
}
