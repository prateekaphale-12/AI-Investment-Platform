import { Suspense, lazy } from "react";
import { Link, Route, Routes } from "react-router-dom";

import { HomePage } from "./pages/HomePage";

const WatchlistPage = lazy(() =>
  import("./pages/WatchlistPage").then((m) => ({ default: m.WatchlistPage })),
);
const AboutPage = lazy(() =>
  import("./pages/AboutPage").then((m) => ({ default: m.AboutPage })),
);

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/" className="text-lg font-semibold tracking-tight text-white">
            AI Investment Research
          </Link>
          <nav className="flex gap-6 text-sm text-slate-300">
            <Link to="/" className="hover:text-white">
              Home
            </Link>
            <Link to="/watchlist" className="hover:text-white">
              Watchlist
            </Link>
            <Link to="/about" className="hover:text-white">
              About
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-10">
        <Suspense fallback={<div className="text-sm text-slate-400">Loading page…</div>}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/watchlist" element={<WatchlistPage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="border-t border-slate-800/80 py-8 text-center text-xs text-slate-500">
        Decision-support research only. Not financial advice. Not a price prediction service.
      </footer>
    </div>
  );
}
