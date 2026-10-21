export default function DataState({
  loading,
  error,
  retry,
}: {
  loading: boolean;
  error?: string;
  retry: () => void;
}) {
  if (loading)
    return (
      <div className="forge-state forge-state--loading" role="status">
        <strong>Loading season data…</strong>
        <p>Fetching players, match statistics and fixtures.</p>
      </div>
    );
  if (error)
    return (
      <div className="forge-state forge-state--error" role="alert">
        <p>{error}</p>
        <button className="forge-button forge-button--secondary" onClick={retry}>
          Try again
        </button>
      </div>
    );
  return null;
}
