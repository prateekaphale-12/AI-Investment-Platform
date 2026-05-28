import { Suspense, lazy, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Home, 
  History, 
  Star, 
  Settings, 
  Info, 
  User, 
  LogOut, 
  ChevronDown,
  TrendingUp,
  Sparkles
} from "lucide-react";

import { PrivateRoute } from "./components/PrivateRoute";
import { useAuth } from "./context/AuthContext";
import { AuthPage } from "./pages/AuthPage";
import { HomePage } from "./pages/HomePage";
import { LLMSettingsPage } from "./pages/LLMSettingsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { StockDetailPage } from "./pages/StockDetailPage";

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
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const navItems = [
    { path: "/", label: "Home", icon: Home },
    { path: "/history", label: "History", icon: History },
    { path: "/watchlist", label: "Watchlist", icon: Star },
    { path: "/llm-settings", label: "AI Settings", icon: Settings },
    { path: "/about", label: "About", icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex items-center justify-between px-8 py-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg blur-lg opacity-50 group-hover:opacity-75 transition"></div>
            <div className="relative bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-lg">
              <TrendingUp className="h-5 w-5 text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-300 bg-clip-text text-transparent">
              AI Investment Research
            </h1>
            <p className="text-xs text-slate-500">Institutional-Grade Analysis</p>
          </div>
        </Link>

        {/* Navigation */}
        <nav className="hidden lg:flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? "text-white"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeNav"
                    className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20 rounded-lg"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                <Icon className="h-4 w-4 relative z-10" />
                <span className="relative z-10">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Menu */}
        <div className="flex items-center gap-4">
          {isAuthenticated && user ? (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-3 px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:bg-slate-800 hover:border-slate-600 transition group"
              >
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                  <div className="text-left hidden sm:block">
                    <p className="text-sm font-medium text-white">{user.email.split('@')[0]}</p>
                    <p className="text-xs text-slate-400">Account</p>
                  </div>
                </div>
                <ChevronDown className={`h-4 w-4 text-slate-400 transition ${userMenuOpen ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence>
                {userMenuOpen && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setUserMenuOpen(false)}
                    />
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="absolute right-0 mt-2 w-64 rounded-xl border border-slate-700/50 bg-slate-900/95 backdrop-blur-xl shadow-2xl z-50"
                    >
                      <div className="p-4 border-b border-slate-800">
                        <p className="text-sm font-medium text-white">{user.email}</p>
                        <p className="text-xs text-slate-400 mt-1">Premium Account</p>
                      </div>
                      <div className="p-2">
                        <button
                          onClick={() => {
                            doLogout();
                            setUserMenuOpen(false);
                          }}
                          className="flex items-center gap-3 w-full px-4 py-2 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-slate-800 transition"
                        >
                          <LogOut className="h-4 w-4" />
                          <span>Log out</span>
                        </button>
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>
          ) : !isLoginPage ? (
            <Link
              to="/login"
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-sm font-semibold text-white hover:from-indigo-600 hover:to-purple-700 transition shadow-lg shadow-indigo-500/25"
            >
              <Sparkles className="h-4 w-4" />
              <span>Sign in</span>
            </Link>
          ) : null}
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950">
      {/* Animated background gradient */}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-900/20 via-transparent to-transparent"></div>
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-purple-900/20 via-transparent to-transparent"></div>
      </div>
      
      <div className="relative z-10">
        <Header />
        <main className="mx-auto px-8 py-8 max-w-[1920px]">
          <Suspense fallback={
            <div className="flex items-center justify-center py-20">
              <div className="text-sm text-slate-400">Loading page…</div>
            </div>
          }>
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
              path="/history"
              element={
                <PrivateRoute>
                  <HistoryPage />
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
            <Route
              path="/stock/:ticker"
              element={
                <PrivateRoute>
                  <StockDetailPage />
                </PrivateRoute>
              }
            />
            <Route path="/about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="relative z-10 border-t border-slate-800/50 bg-slate-950/80 backdrop-blur-xl py-8 text-center">
        <p className="text-xs text-slate-500">
          Decision-support research only. Not financial advice. Not a price prediction service.
        </p>
        <p className="text-xs text-slate-600 mt-2">
          © 2026 AI Investment Research. All rights reserved.
        </p>
      </footer>
    </div>
    </div>
  );
}
