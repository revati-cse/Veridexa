import type { ReactNode } from "react";
import { Inbox } from "lucide-react";

export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-300 bg-white px-4 py-10 text-center text-slate-500">
      <Inbox size={22} className="text-slate-300" />
      <p className="text-sm">{message}</p>
      {action}
    </div>
  );
}
