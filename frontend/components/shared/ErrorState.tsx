import { AlertTriangle } from "lucide-react";
import { Button } from "./Button";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-4 text-rose-900">
      <AlertTriangle size={18} className="mt-0.5 shrink-0 text-rose-600" />
      <div className="flex flex-col gap-2">
        <div>
          <p className="text-sm font-semibold">Something went wrong</p>
          <p className="mt-0.5 text-sm text-rose-700">{message}</p>
        </div>
        {onRetry && (
          <Button
            onClick={onRetry}
            variant="secondary"
            className="self-start border-rose-300 bg-white px-3 py-1.5 text-xs text-rose-700 hover:bg-rose-100"
          >
            Retry
          </Button>
        )}
      </div>
    </div>
  );
}
