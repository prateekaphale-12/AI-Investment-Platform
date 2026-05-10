type Props = {
  label?: string;
  detail?: string;
};

export function LoadingIndicator({ label = "Analyzing…", detail }: Props) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-slate-800 bg-slate-900/60 px-5 py-4">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
      <div>
        <p className="text-sm font-medium text-white">{label}</p>
        {detail ? <p className="mt-1 text-xs text-slate-400">{detail}</p> : null}
      </div>
    </div>
  );
}
