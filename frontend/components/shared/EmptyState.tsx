export function EmptyState({ message, action }: { message: string; action?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-8 text-center text-slate-500">
      <p>{message}</p>
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}
