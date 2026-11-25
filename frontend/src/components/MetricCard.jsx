export default function MetricCard({ label, value, note, icon, accent }) {
  return (
    <article className={`metric-card ${accent ? "metric-card-accent" : ""}`}>
      <div className="metric-card-top"><span className="metric-icon">{icon}</span><span className="metric-note">{note}</span></div>
      <div className="metric-value">{value}</div>
      <div className="metric-label">{label}</div>
    </article>
  );
}
