import { useEffect, useState } from "react";
import { api } from "../api";
import { History, Home } from "lucide-react";

interface AnalysisItem {
  id: string;
  status: string;
  summary: {
    total_budget: number;
    total_expected_return: number;
    overall_risk: string;
    diversification_score: number;
    best_performer: string | null;
  } | null;
  created_at: string;
  completed_at: string | null;
}

export function HistoryPage() {
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    loadAnalyses();
  }, []);

  async function loadAnalyses() {
    try {
      setLoading(true);
      setError(null);
      const { data } = await api.get<{ items: AnalysisItem[] }>("/api/v1/analysis?limit=50&offset=0");
      console.log("Loaded analyses:", data);
      setAnalyses(data.items || []);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || "Failed to load analysis history";
      setError(errorMessage);
      console.error("Failed to load analyses:", err);
    } finally {
      setLoading(false);
    }
  }

  async function downloadPDF(sessionId: string) {
    try {
      setDownloading(sessionId);
      const response = await api.get(`/api/v1/analysis/${sessionId}/export/pdf`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `analysis-${sessionId.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download PDF");
      console.error(err);
    } finally {
      setDownloading(null);
    }
  }

  async function deleteAnalysis(sessionId: string) {
    if (!confirm("Are you sure you want to delete this analysis?")) return;
    try {
      await api.delete(`/api/v1/analysis/${sessionId}`);
      setAnalyses(analyses.filter((a) => a.id !== sessionId));
    } catch (err) {
      alert("Failed to delete analysis");
      console.error(err);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-indigo-500 border-r-transparent mb-4"></div>
          <p className="text-slate-400">Loading analysis history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6">
          <h3 className="text-lg font-semibold text-red-400 mb-2">Error Loading History</h3>
          <p className="text-red-300">{error}</p>
          <button
            onClick={loadAnalyses}
            className="mt-4 px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700 transition"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-12 text-center">
          <div className="mb-4">
            <History className="h-16 w-16 text-slate-600 mx-auto" />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">No Analysis History</h3>
          <p className="text-slate-400 mb-6">
            You haven't run any analyses yet. Start by running an analysis on the home page.
          </p>
          <a
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 transition"
          >
            <Home className="h-4 w-4" />
            Go to Home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-white">Analysis History</h1>
        <p className="mt-2 text-slate-400">View and manage your past analyses</p>
      </div>

      <div className="space-y-3">
        {analyses.map((analysis) => (
          <div
            key={analysis.id}
            className="rounded-lg border border-slate-700 bg-slate-800/50 p-4 hover:bg-slate-800/70 transition"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-sm font-mono text-slate-400">{analysis.id.slice(0, 8)}</span>
                  <span
                    className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                      analysis.status === "completed"
                        ? "bg-emerald-500/20 text-emerald-300"
                        : analysis.status === "failed"
                          ? "bg-red-500/20 text-red-300"
                          : "bg-yellow-500/20 text-yellow-300"
                    }`}
                  >
                    {analysis.status}
                  </span>
                </div>

                {analysis.summary && (
                  <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
                    <div>
                      <p className="text-slate-500">Budget</p>
                      <p className="font-semibold text-white">
                        ${((analysis.summary.total_budget ?? 0) / 1000).toFixed(1)}k
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Expected Return</p>
                      <p className="font-semibold text-emerald-400">
                        {(analysis.summary.total_expected_return ?? 0).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Risk</p>
                      <p className="font-semibold text-white capitalize">
                        {analysis.summary.overall_risk ?? "N/A"}
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Diversification</p>
                      <p className="font-semibold text-white">
                        {(analysis.summary.diversification_score ?? 0).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                )}

                <p className="mt-2 text-xs text-slate-500">
                  Created: {new Date(analysis.created_at).toLocaleDateString()} at{" "}
                  {new Date(analysis.created_at).toLocaleTimeString()}
                </p>
              </div>

              <div className="flex flex-col gap-2">
                <button
                  onClick={() => downloadPDF(analysis.id)}
                  disabled={downloading === analysis.id}
                  className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {downloading === analysis.id ? "Downloading..." : "Download PDF"}
                </button>
                <button
                  onClick={() => deleteAnalysis(analysis.id)}
                  className="rounded bg-red-600/20 px-3 py-1.5 text-xs font-medium text-red-300 hover:bg-red-600/30 transition"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
