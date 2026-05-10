import ReactMarkdown from "react-markdown";

export function AIReport({ markdown }: { markdown: string }) {
  if (!markdown) return null;
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-sm leading-relaxed text-slate-200 [&_h1]:mb-4 [&_h1]:text-2xl [&_h1]:font-semibold [&_h1]:text-white [&_h2]:mt-6 [&_h2]:mb-2 [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-white [&_h3]:mt-4 [&_h3]:font-medium [&_h3]:text-slate-100 [&_li]:my-1 [&_p]:my-3 [&_strong]:text-white [&_ul]:list-disc [&_ul]:pl-5 [&_hr]:border-slate-700">
      <ReactMarkdown>{markdown}</ReactMarkdown>
    </div>
  );
}
