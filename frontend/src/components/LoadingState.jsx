export default function LoadingState({ error }) {
  return <div className={error ? "state-message state-error" : "state-message"}>{error || "Loading your analytics…"}</div>;
}
