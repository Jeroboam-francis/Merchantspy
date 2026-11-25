const COLORS = ["#ff0000", "#282d35", "#8e97a4", "#e7a5a5"];

export default function TrendChart({ series = [], title, subtitle = "Daily performance" }) {
  const entries = Object.entries(series).sort(([a], [b]) => a.localeCompare(b));
  const max = Math.max(1, ...entries.map(([, value]) => Number(value)));
  const points = entries.map(([, value], index) => {
    const x = entries.length < 2 ? 0 : (index / (entries.length - 1)) * 100;
    const y = 94 - (Number(value) / max) * 82;
    return `${x},${y}`;
  }).join(" ");
  return (
    <section className="panel trend-panel">
      <div className="panel-heading"><div><h2>{title}</h2><p>{subtitle}</p></div><span className="chart-legend"><i /> This period</span></div>
      {entries.length ? (
        <div className="chart-wrap" role="img" aria-label={`${title} line chart`}>
          <div className="chart-y-labels"><span>{max.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span><span>{Math.round(max / 2).toLocaleString("en-IN")}</span><span>0</span></div>
          <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="line-chart">
            {[12, 53, 94].map((y) => <line key={y} x1="0" x2="100" y1={y} y2={y} className="grid-line" />)}
            <polyline points={points} fill="none" stroke={COLORS[0]} strokeWidth="1.7" vectorEffect="non-scaling-stroke" />
          </svg>
          <div className="chart-x-labels"><span>{entries[0][0]}</span><span>{entries[Math.floor(entries.length / 2)][0]}</span><span>{entries.at(-1)[0]}</span></div>
        </div>
      ) : <div className="empty-chart">No activity for the selected period</div>}
    </section>
  );
}
