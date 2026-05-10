import { FormEvent, useState } from "react";

import type { AnalyzePayload } from "../api";

type Props = {
  onSubmit: (payload: AnalyzePayload) => void;
  disabled?: boolean;
};

const SECTORS = [
  "Technology",
  "Semiconductors",
  "Healthcare",
  "Financials",
  "Consumer",
  "Energy",
];

export function QueryForm({ onSubmit, disabled }: Props) {
  const [budget, setBudget] = useState(50000);
  const [risk, setRisk] = useState<AnalyzePayload["risk_tolerance"]>("medium");
  const [horizon, setHorizon] = useState("1y");
  const [goal, setGoal] = useState<AnalyzePayload["goal"]>("growth");
  const [selected, setSelected] = useState<string[]>(["Technology", "Semiconductors"]);

  function toggleSector(s: string) {
    setSelected((prev) => (prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s]));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    onSubmit({
      budget,
      risk_tolerance: risk,
      investment_horizon: horizon,
      interests: selected,
      goal,
    });
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6 shadow-xl shadow-slate-950/40"
    >
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-white">Tell us your preferences</h2>
        <p className="mt-1 text-sm text-slate-400">We’ll run multi-step research and surface explainable outputs.</p>
      </div>

      <div className="space-y-5">
        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Budget (USD)</label>
          <input
            type="range"
            min={5000}
            max={500000}
            step={1000}
            value={budget}
            onChange={(ev) => setBudget(Number(ev.target.value))}
            className="w-full accent-indigo-500"
            disabled={disabled}
          />
          <div className="mt-1 text-sm text-slate-400">${budget.toLocaleString()}</div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">Risk tolerance</label>
            <select
              value={risk}
              onChange={(e) => setRisk(e.target.value as AnalyzePayload["risk_tolerance"])}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              disabled={disabled}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">Horizon</label>
            <select
              value={horizon}
              onChange={(e) => setHorizon(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
              disabled={disabled}
            >
              <option value="3m">3 months</option>
              <option value="6m">6 months</option>
              <option value="1y">1 year</option>
              <option value="3y">3 years</option>
            </select>
          </div>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Goal</label>
          <select
            value={goal}
            onChange={(e) => setGoal(e.target.value as AnalyzePayload["goal"])}
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white"
            disabled={disabled}
          >
            <option value="growth">Growth</option>
            <option value="income">Income</option>
            <option value="balanced">Balanced</option>
          </select>
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-slate-300">Sector focus</label>
          <div className="flex flex-wrap gap-2">
            {SECTORS.map((s) => {
              const active = selected.includes(s);
              return (
                <button
                  key={s}
                  type="button"
                  onClick={() => toggleSector(s)}
                  disabled={disabled}
                  className={
                    active
                      ? "rounded-full border border-indigo-500 bg-indigo-500/15 px-3 py-1 text-xs font-medium text-indigo-200"
                      : "rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs font-medium text-slate-300 hover:border-slate-600"
                  }
                >
                  {s}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <button
        type="submit"
        disabled={disabled || selected.length === 0}
        className="mt-6 w-full rounded-xl bg-indigo-500 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-400 disabled:cursor-not-allowed disabled:opacity-50"
      >
        Run analysis
      </button>
    </form>
  );
}
