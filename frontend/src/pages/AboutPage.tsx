import { Link } from "react-router-dom";

export function AboutPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-3xl font-semibold text-white">About</h1>
      <div className="space-y-4 text-sm leading-relaxed text-slate-300">
        <p>
          This prototype is <strong className="text-white">research software</strong>, not a broker and not personalised
          financial advice. It does not predict prices and should not be used as the sole basis for investment decisions.
        </p>
        <p>
          <strong className="text-white">Data &amp; determinism:</strong> prices and fundamentals come from{" "}
          <code className="rounded bg-slate-800 px-1">yfinance</code>; RSI, MACD, and SMAs are computed in Python; portfolio weights
          use rule-based logic. The LLM is only asked to turn those facts into readable narrative.
        </p>
        <p>
          <strong className="text-white">Without an API key:</strong> you still get allocations, charts, and structured rationale
          strings; the long memo may be a placeholder that embeds the same fact block the model would receive.
        </p>
      </div>
      <Link to="/" className="inline-block text-sm font-medium text-indigo-300 hover:text-indigo-200">
        ← Back to dashboard
      </Link>
    </div>
  );
}
