import { useMemo, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import MetricCard from "../components/MetricCard.jsx";
import TrendChart from "../components/TrendChart.jsx";
import LoadingState from "../components/LoadingState.jsx";
import { useApi } from "../hooks/useApi.js";
import { downloadReport, getJson } from "../services/api.js";
import { saveView, setRange, setWidget } from "../store.js";
import "./Dashboard.css";

const money = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function Dashboard() {
  const dispatch = useDispatch();
  const range = useSelector((state) => state.view.range);
  const savedViews = useSelector((state) => state.view.savedViews);
  const widgets = useSelector((state) => state.view.widgets);
  const [builderOpen, setBuilderOpen] = useState(false);
  const { signals, signalsError } = useOutletContext();
  const [exportError, setExportError] = useState("");
  const days = Number(range.replace("d", ""));
  const start = useMemo(() => new Date(Date.now() - (days - 1) * 86400000).toISOString().slice(0, 10), [days]);
  const end = new Date().toISOString().slice(0, 10);
  const { data: overview, loading: overviewLoading, error: overviewError } = useApi(() => getJson(`/analytics/overview?start=${start}&end=${end}`), [start, end], 60000);
  const { data: trends, loading: trendsLoading, error: trendsError } = useApi(() => getJson(`/analytics/trends?days=${days}`), [days], 60000);
  const { data: ranking } = useApi(() => getJson("/analytics/ranking?limit=5"), []);
  const { data: geography } = useApi(() => getJson("/analytics/geography"), []);
  async function exportFile(format) {
    try { setExportError(""); await downloadReport(format); }
    catch (error) { setExportError(error.message); }
  }
  const maxRegion = Math.max(1, ...(geography || []).map((row) => row.revenue));
  return (
    <div className="dashboard-page">
      <div className="page-heading">
        <div><p className="eyebrow">OVERVIEW / BUSINESS PERFORMANCE</p><h1>Executive dashboard</h1><p className="page-subtitle">A real-time view of your merchant network.</p></div>
        <div className="heading-actions">
          <select aria-label="Reporting period" value={range} onChange={(event) => dispatch(setRange(event.target.value))}><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="90d">Last 90 days</option></select>
          <button className="outline-button" onClick={() => dispatch(saveView(`Executive · ${range}`))}>{savedViews.includes(`Executive · ${range}`) ? "★ Saved view" : "☆ Save view"}</button>
          {savedViews.length > 0 && <select aria-label="Saved views" value="" onChange={(event) => dispatch(setRange(event.target.value.split("·").pop().trim()))}><option value="">Bookmarks ({savedViews.length})</option>{savedViews.map((view) => <option key={view} value={view}>{view}</option>)}</select>}
          <button className="outline-button" onClick={() => setBuilderOpen((open) => !open)}>{builderOpen ? "Close builder" : "Customize"}</button>
          <div className="export-menu"><button className="primary-button" onClick={() => exportFile("xlsx")}>Export report ↓</button><div className="export-options"><button onClick={() => exportFile("csv")}>CSV</button><button onClick={() => exportFile("xlsx")}>Excel</button><button onClick={() => exportFile("pdf")}>PDF</button></div></div>
        </div>
        {builderOpen && <section className="builder-panel panel"><b>Dashboard builder</b><span>Choose trend widgets to display</span>{[["revenue", "Revenue"], ["collections", "Collections"], ["disbursements", "Disbursements"], ["activity", "Merchant activity"]].map(([key, label]) => <label key={key}><input type="checkbox" checked={widgets.includes(key)} onChange={(event) => dispatch(setWidget({ name: key, enabled: event.target.checked }))} />{label}</label>)}</section>}
      </div>
      {overviewError && <div className="banner-error">{overviewError}</div>}
      {overviewLoading ? <LoadingState error={overviewError} /> : overview && <section className="metric-grid">
        <MetricCard label="Total revenue" value={money(overview.total_revenue)} note="Successful transactions" icon="₹" accent />
        <MetricCard label="Total collections" value={money(overview.total_collections)} note="Across merchant network" icon="↘" />
        <MetricCard label="Total disbursements" value={money(overview.total_disbursements)} note="Processed payouts" icon="↗" />
        <MetricCard label="Revenue / collection" value={overview.revenue_to_collection_ratio?.toFixed(2) ?? "—"} note="Revenue-to-collection ratio" icon="÷" />
        <MetricCard label="Revenue / disbursement" value={overview.revenue_to_disbursement_ratio?.toFixed(2) ?? "—"} note="Revenue-to-disbursement ratio" icon="÷" />
        <MetricCard label="Active merchants" value={Number(overview.active_merchants).toLocaleString("en-IN")} note="Currently trading" icon="♙" />
        <MetricCard label="Dormant merchants" value={Number(overview.dormant_merchants).toLocaleString("en-IN")} note="Inactive portfolio" icon="◌" />
        <MetricCard label="Unique subscribers" value={Number(overview.unique_subscribers).toLocaleString("en-IN")} note="Active subscribers" icon="♧" />
      </section>}
      {exportError && <div className="banner-error">{exportError}</div>}
      <section className="chart-grid">
        {trendsLoading ? <div className="panel"><LoadingState error={trendsError} /></div> : trends && <>
          {widgets.includes("revenue") && <TrendChart title="Revenue trend" series={trends.revenue} />}
          {widgets.includes("collections") && <TrendChart title="Collection trend" series={trends.collections} />}
          {widgets.includes("disbursements") && <TrendChart title="Disbursement trend" series={trends.disbursements} />}
          {widgets.includes("activity") && <TrendChart title="Merchant activity" subtitle="Unique merchants transacting each day" series={trends.merchant_activity} />}
        </>}
      </section>
      <section className="lower-grid">
        <div className="panel">
          <div className="panel-heading"><div><h2>Top performing merchants</h2><p>Ranked by merchant performance score</p></div><Link className="subtle-link" to="/analytics">View all →</Link></div>
          <div className="table-scroll"><table><thead><tr><th>MERCHANT</th><th>REVENUE</th><th>SCORE</th><th>GRADE</th></tr></thead><tbody>
            {(ranking?.top || []).map((row) => <tr key={row.id}><td><Link className="merchant-link" to={`/merchants/${row.id}`}><span className="merchant-initial">{row.name.slice(0, 1)}</span><span>{row.name}<small>{row.code} · {row.region}</small></span></Link></td><td>{money(row.revenue)}</td><td>{row.score}</td><td><span className={`grade grade-${row.grade.replace("+", "plus")}`}>{row.grade}</span></td></tr>)}
            {!ranking?.top?.length && <tr><td colSpan="4" className="table-empty">Seed demo data to view merchant rankings.</td></tr>}
          </tbody></table></div>
        </div>
        <div className="panel geography-panel">
          <div className="panel-heading"><div><h2>Geographical distribution</h2><p>Revenue by operating region</p></div><span className="globe-icon">◎</span></div>
          <div className="region-list">{(geography || []).map((region) => <Link className="region-row region-link" to={`/analytics?region=${encodeURIComponent(region.region)}`} key={region.region}><div className="region-name"><span>{region.region}</span><b>{money(region.revenue)}</b></div><div className="region-track"><div style={{ width: `${Math.max(3, region.revenue / maxRegion * 100)}%` }} /></div></Link>)}
            {!geography?.length && <p className="table-empty">Region insights appear when data is available.</p>}
          </div>
          <div className="ratio-footer"><span>Network anomaly signals</span><b>{signals?.anomalies?.length ?? "—"} active</b></div>
        </div>
      </section>
      <section className="lower-grid portfolio-insights">
        <div className="panel">
          <div className="panel-heading"><div><h2>Lowest performing merchants</h2><p>Merchants to review by portfolio score</p></div><Link className="subtle-link" to="/analytics">Portfolio →</Link></div>
          <div className="table-scroll"><table><thead><tr><th>MERCHANT</th><th>REVENUE</th><th>SCORE</th><th>GRADE</th></tr></thead><tbody>
            {(ranking?.lowest || []).map((row) => <tr key={row.id}><td><Link className="merchant-link" to={`/merchants/${row.id}`}><span className="merchant-initial">{row.name.slice(0, 1)}</span><span>{row.name}<small>{row.code} · {row.region}</small></span></Link></td><td>{money(row.revenue)}</td><td>{row.score}</td><td><span className={`grade grade-${row.grade.replace("+", "plus")}`}>{row.grade}</span></td></tr>)}
            {!ranking?.lowest?.length && <tr><td colSpan="4" className="table-empty">Seed demo data to view portfolio performance.</td></tr>}
          </tbody></table></div>
        </div>
        <div className="panel">
          <div className="panel-heading"><div><h2>Activity alerts</h2><p>Daily spikes and drops versus a rolling 7-day baseline</p></div></div>
          {(signals?.spikes_and_drops || []).slice(0, 6).map((signal, index) => <div className="activity-alert" key={`${signal.date}-${index}`}><span className={signal.type === "spike" ? "alert-badge alert-spike" : "alert-badge"}>{signal.type}</span><span><b>{signal.date}</b><small>₹{Number(signal.value).toLocaleString("en-IN")} · z {Number(signal.z_score).toFixed(1)}</small></span></div>)}
          {!signals?.spikes_and_drops?.length && <p className="table-empty">{signalsError ? `Signal analysis unavailable: ${signalsError}` : signals ? "No significant spikes or drops detected." : "Signals are loading."}</p>}
        </div>
      </section>
    </div>
  );
}
