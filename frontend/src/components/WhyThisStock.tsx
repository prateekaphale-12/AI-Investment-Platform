import { useState } from "react";
import { ExternalLink } from "lucide-react";

export type KeyHeadline = {
  headline: string;
  source: string;
  url: string;
  sentiment: string;
  published_at: string;
};

export type SentimentData = {
  label: string;
  news_summary: string;
  key_headlines: KeyHeadline[];
  compound?: number;
  headlines_used?: number;
  event_types?: string[];
};

export type Rationale = {
  market_trend?: string;
  technical?: string;
  sentiment?: string | SentimentData;
  fundamentals?: string;
  risk?: string;
  summary?: string;
};

export function WhyThisStock({ ticker, rationale }: { ticker: string; rationale: Rationale }) {
  const [open, setOpen] = useState(false);

  // Helper to check if sentiment is a SentimentData object
  const isSentimentData = (sent: any): sent is SentimentData => {
    return typeof sent === "object" && sent !== null && "label" in sent;
  };

  const sentimentData = isSentimentData(rationale.sentiment) ? rationale.sentiment : null;
  const sentimentText = typeof rationale.sentiment === "string" ? rationale.sentiment : "";

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
        <div className="space-y-3 border-t border-slate-800/80 px-3 py-3 text-sm text-slate-300">
          <p>
            <span className="font-medium text-emerald-300">Market:</span> {rationale.market_trend}
          </p>
          <p>
            <span className="font-medium text-sky-300">Technical:</span> {rationale.technical}
          </p>

          {/* Enhanced Sentiment Display */}
          <div>
            <span className="font-medium text-amber-200">Sentiment:</span>
            {sentimentData ? (
              <div className="mt-2 space-y-2">
                {/* Sentiment Label */}
                <p className="text-sm">
                  <span className="font-semibold capitalize text-amber-300">{sentimentData.label}</span>
                </p>

                {/* News Summary */}
                {sentimentData.news_summary && (
                  <div className="rounded-md bg-slate-900/50 p-2 italic text-slate-200">
                    <p className="text-xs font-medium text-slate-400 mb-1">Summary based on news:</p>
                    <p>{sentimentData.news_summary}</p>
                  </div>
                )}

                {/* Key Headlines */}
                {sentimentData.key_headlines && sentimentData.key_headlines.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-slate-400 mb-1">Key Headlines:</p>
                    <ul className="space-y-1">
                      {sentimentData.key_headlines.map((headline, idx) => (
                        <li key={idx} className="text-xs">
                          {headline.url ? (
                            <a
                              href={headline.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-start gap-1 text-blue-400 hover:text-blue-300 hover:underline"
                            >
                              <span className="flex-1">{headline.headline}</span>
                              <ExternalLink className="w-3 h-3 flex-shrink-0 mt-0.5" />
                            </a>
                          ) : (
                            <span>{headline.headline}</span>
                          )}
                          <div className="text-slate-500 mt-0.5">
                            {headline.source} • {headline.sentiment}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="ml-2">{sentimentText}</p>
            )}
          </div>

          <p>
            <span className="font-medium text-teal-200">Fundamentals:</span> {rationale.fundamentals}
          </p>
          <p>
            <span className="font-medium text-rose-300">Risk:</span> {rationale.risk}
          </p>
          {rationale.summary ? (
            <p className="rounded-md bg-slate-900/70 p-2 text-sm italic text-slate-200">
              "{rationale.summary}"
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
