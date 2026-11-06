export function LoadingState() {
  return <p className="rounded border border-slate-200 bg-white p-4 text-sm text-slate-600">Loading protected data…</p>;
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <strong>Protected data unavailable:</strong> {message}
      {onRetry && <button className="ml-3 underline" onClick={onRetry}>Retry</button>}
    </div>
  );
}
