import { useState } from "react";

export type Rationale = {
  market_trend?: string;
  technical?: string;
  sentiment?: string;
  fundamentals?: string;
  risk?: string;
  summary?: string;
};

export function WhyThisStock({ ticker, rationale }: { ticker: string; rationale: Rationale }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-3 rounded-lg border border-slate-800/80 bg-slate-950/40">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-indigo-200"
      >
        Why this stock? — {ticker}
        <span className="text-slate-500">{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <div className="space-y-2 border-t border-slate-800/80 px-3 py-3 text-sm text-slate-300">
          <p>
            <span className="font-medium text-emerald-300">Market:</span> {rationale.market_trend}
          </p>
          <p>
            <span className="font-medium text-sky-300">Technical:</span> {rationale.technical}
          </p>
          <p>
            <span className="font-medium text-amber-200">Sentiment:</span> {rationale.sentiment}
          </p>
          <p>
            <span className="font-medium text-teal-200">Fundamentals:</span> {rationale.fundamentals}
          </p>
          <p>
            <span className="font-medium text-rose-300">Risk:</span> {rationale.risk}
          </p>
          {rationale.summary ? (
            <p className="rounded-md bg-slate-900/70 p-2 text-sm italic text-slate-200">
              “{rationale.summary}”
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
