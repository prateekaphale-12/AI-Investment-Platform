import { Suspense, lazy } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { PrivateRoute } from "./components/PrivateRoute";
import { useAuth } from "./context/AuthContext";
import { AuthPage } from "./pages/AuthPage";
import { HomePage } from "./pages/HomePage";
import { LLMSettingsPage } from "./pages/LLMSettingsPage";

const WatchlistPage = lazy(() =>
  import("./pages/WatchlistPage").then((m) => ({ default: m.WatchlistPage })),
);
const AboutPage = lazy(() =>
  import("./pages/AboutPage").then((m) => ({ default: m.AboutPage })),
);

function Header() {
  const { isAuthenticated, user, doLogout } = useAuth();
  const location = useLocation();
  const isLoginPage = location.pathname === "/login";

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
        <Link to="/" className="text-lg font-semibold tracking-tight text-white">
          AI Investment Research
        </Link>
        <div className="flex items-center gap-6">
          <nav className="flex gap-6 text-sm text-slate-300">
            <Link to="/" className="hover:text-white">
              Home
            </Link>
            <Link to="/watchlist" className="hover:text-white">
              Watchlist
            </Link>
            <Link to="/llm-settings" className="hover:text-white">
              AI Settings
            </Link>
            <Link to="/about" className="hover:text-white">
              About
            </Link>
          </nav>
          <div className="flex items-center gap-3">
            {isAuthenticated && user ? (
              <>
                <span className="text-xs text-emerald-300">{user.email}</span>
                <button
                  type="button"
                  onClick={doLogout}
                  className="rounded border border-slate-600 px-2 py-1 text-xs text-slate-300 hover:bg-slate-800"
                >
                  Log out
                </button>
              </>
            ) : !isLoginPage ? (
              <Link
                to="/login"
                className="rounded bg-indigo-500 px-2 py-1 text-xs font-medium text-white hover:bg-indigo-600"
              >
                Sign in
              </Link>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      <Header />
      <main className="mx-auto max-w-6xl px-4 py-10">
        <Suspense fallback={<div className="text-sm text-slate-400">Loading page…</div>}>
          <Routes>
            <Route path="/login" element={<AuthPage />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <HomePage />
                </PrivateRoute>
              }
            />
            <Route
              path="/watchlist"
              element={
                <PrivateRoute>
                  <WatchlistPage />
                </PrivateRoute>
              }
            />
            <Route
              path="/llm-settings"
              element={
                <PrivateRoute>
                  <LLMSettingsPage />
                </PrivateRoute>
              }
            />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="border-t border-slate-800/80 py-8 text-center text-xs text-slate-500">
        Decision-support research only. Not financial advice. Not a price prediction service.
      </footer>
    </div>
  );
}
