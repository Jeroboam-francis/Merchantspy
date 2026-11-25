import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import MetricCard from "../components/MetricCard.jsx";
import TrendChart from "../components/TrendChart.jsx";
import LoadingState from "../components/LoadingState.jsx";
import { useApi } from "../hooks/useApi.js";
import { getJson } from "../services/api.js";
import "./MerchantDetails.css";

const money = (value) => `₹${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function MerchantDetails() {
  const { merchantId } = useParams();
  const [period, setPeriod] = useState("monthly");
  const { data, loading, error } = useApi(() => getJson(`/merchants/${merchantId}?period=${period}`), [merchantId, period]);
  if (loading) return <LoadingState />;
  if (error) return <LoadingState error={error} />;
  const trend = Object.fromEntries((data.period_analysis || []).map((row) => [row.period, row.revenue]));
  return (
    <div className="merchant-details-page">
      <div className="page-heading"><div><p className="eyebrow"><Link to="/analytics">MERCHANTS</Link> / PROFILE</p><h1>{data.profile.name}</h1><p className="page-subtitle">{data.profile.code} · {data.profile.category} · {data.profile.region}</p></div>
        <div className="heading-actions"><select aria-label="Analysis granularity" value={period} onChange={(event) => setPeriod(event.target.value)}><option value="daily">Daily</option><option value="monthly">Monthly</option><option value="yearly">Yearly</option></select><span className={`status-pill status-${data.profile.status}`}>{data.profile.status}</span></div>
      </div>
      <section className="metric-grid">
        <MetricCard label="Merchant revenue" value={money(data.revenue)} note="Successful transactions" icon="₹" accent />
        <MetricCard label="Transactions" value={Number(data.transactions).toLocaleString("en-IN")} note="All transaction attempts" icon="▤" />
        <MetricCard label="Collections" value={money(data.collections)} note="Successfully collected" icon="↘" />
        <MetricCard label="Disbursements" value={money(data.disbursements)} note={`${data.subscribers.toLocaleString("en-IN")} active subscribers`} icon="↗" />
      </section>
      <section className="chart-grid detail-chart-grid"><TrendChart title={`${period[0].toUpperCase()}${period.slice(1)} revenue`} subtitle="Merchant revenue performance" series={trend} />
        <div className="panel score-panel"><div className="panel-heading"><div><h2>Merchant score</h2><p>Composite portfolio performance</p></div></div><div className="score-display"><strong>{data.score}</strong><span>/ 100</span></div><span className={`grade grade-${data.grade.replace("+", "plus")}`}>{data.grade}</span><p className="merchant-rank">Portfolio rank <b>#{data.ranking ?? "—"}</b> of {data.portfolio_size}</p><div className="score-breakdown"><div><span>Transactions</span><b>{data.transactions.toLocaleString("en-IN")}</b></div><div><span>Subscribers</span><b>{data.subscribers.toLocaleString("en-IN")}</b></div><div><span>Growth rate</span><b>{data.growth_rate}%</b></div></div></div>
      </section>
      <section className="panel transaction-panel"><div className="panel-heading"><div><h2>Recent transactions</h2><p>Latest 100 transaction events</p></div><span className="count-pill">{data.recent_transactions.length} records</span></div><div className="table-scroll"><table><thead><tr><th>REFERENCE</th><th>DATE & TIME</th><th>CHANNEL</th><th>STATUS</th><th>AMOUNT</th></tr></thead><tbody>
        {data.recent_transactions.map((row) => <tr key={row.id}><td className="reference-cell">{row.reference}</td><td>{new Date(row.date).toLocaleString()}</td><td>{row.channel}</td><td><span className={`status-pill status-${row.status}`}>{row.status}</span></td><td>{money(row.amount)}</td></tr>)}
        {!data.recent_transactions.length && <tr><td colSpan="5" className="table-empty">No transaction data. Seed the development database to explore this merchant.</td></tr>}
      </tbody></table></div></section>
    </div>
  );
}
