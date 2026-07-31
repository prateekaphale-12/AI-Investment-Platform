/**
 * Skeleton loader for market snapshot
 * Shows while snapshot data is loading
 */
export function SnapshotSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Top Picks & Market Overview Skeleton */}
      <div className="grid gap-4 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <div className="mb-3 h-3 w-20 rounded bg-slate-700"></div>
            <div className="space-y-3">
              {[1, 2, 3].map((j) => (
                <div key={j} className="flex items-center justify-between">
                  <div className="h-4 w-12 rounded bg-slate-700"></div>
                  <div className="h-4 w-16 rounded bg-slate-700"></div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* News Section Skeleton */}
      <div className="space-y-4">
        <div className="h-4 w-40 rounded bg-slate-700"></div>
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="space-y-2">
              <div className="h-8 rounded bg-slate-800/50"></div>
              {[1, 2].map((j) => (
                <div key={j} className="space-y-2 rounded-lg border border-slate-700 bg-slate-800/30 p-3">
                  <div className="h-3 w-full rounded bg-slate-700"></div>
                  <div className="h-3 w-3/4 rounded bg-slate-700"></div>
                  <div className="flex gap-2">
                    <div className="h-3 w-20 rounded bg-slate-700"></div>
                    <div className="h-3 w-16 rounded bg-slate-700"></div>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Market News Skeleton */}
      <div className="space-y-4">
        <div className="h-4 w-40 rounded bg-slate-700"></div>
        <div className="space-y-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex gap-4 rounded-lg border border-slate-700 bg-slate-800/30 p-4">
              <div className="h-20 w-20 flex-shrink-0 rounded-lg bg-slate-700"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 w-full rounded bg-slate-700"></div>
                <div className="h-3 w-3/4 rounded bg-slate-700"></div>
                <div className="flex gap-2">
                  <div className="h-3 w-24 rounded bg-slate-700"></div>
                  <div className="h-3 w-16 rounded bg-slate-700"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
