import { Loader2 } from "lucide-react";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-6 text-slate-500">
      <Loader2 size={18} className="shrink-0 animate-spin text-indigo-500" />
      <span className="text-sm">{label}</span>
    </div>
  );
}
