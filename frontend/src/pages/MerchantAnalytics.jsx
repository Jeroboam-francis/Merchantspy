import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useSelector } from "react-redux";
import LoadingState from "../components/LoadingState.jsx";
import { useApi } from "../hooks/useApi.js";
import { getJson } from "../services/api.js";
import { useDispatch } from "react-redux";
import { setSearch } from "../store.js";
import "./MerchantAnalytics.css";

export default function MerchantAnalytics() {
  const dispatch = useDispatch();
  const [searchParams, setSearchParams] = useSearchParams();
  const search = useSelector((state) => state.view.search);
  const [status, setStatus] = useState("");
  const region = searchParams.get("region") || "";
  const { data: regions } = useApi(() => getJson("/analytics/regions"), []);
  const query = useMemo(() => `/merchants?limit=100${search ? `&search=${encodeURIComponent(search)}` : ""}${status ? `&status=${status}` : ""}${region ? `&region=${encodeURIComponent(region)}` : ""}`, [search, status, region]);
  const { data, loading, error } = useApi(() => getJson(query), [query]);
  const { data: ranking } = useApi(() => getJson("/analytics/ranking?limit=5"), []);
  const { data: segments } = useApi(() => getJson("/analytics/segments"), []);
  return (
    <div className="merchant-analytics-page">
      <div className="page-heading"><div><p className="eyebrow">WORKSPACE / MERCHANTS</p><h1>Merchant analytics</h1><p className="page-subtitle">Explore portfolio performance, segment leaders, and follow through to merchant detail.</p></div>
        <span className="count-pill">{data?.total ?? "—"} merchants</span>
      </div>
      <div className="filter-bar panel">
        <label className="search-field"><span>⌕</span><input aria-label="Search merchants" placeholder="Search merchant or code" value={search} onChange={(event) => dispatch(setSearch(event.target.value))} /></label>
        <select aria-label="Merchant status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="dormant">Dormant</option></select>
        <select aria-label="Merchant region" value={region} onChange={(event) => { const next = new URLSearchParams(searchParams); if (event.target.value) next.set("region", event.target.value); else next.delete("region"); setSearchParams(next); }}><option value="">All regions</option>{(regions || []).map((item) => <option key={item.id} value={item.name}>{item.name}</option>)}</select>
        <span className="filter-hint">Use filters to narrow your portfolio</span>
      </div>
      <section className="lower-grid analytics-layout">
        <div className="panel merchant-table-panel"><div className="panel-heading"><div><h2>Merchant portfolio</h2><p>Revenue, transactions and merchant score</p></div></div>
          {loading ? <LoadingState /> : error ? <LoadingState error={error} /> : <div className="table-scroll"><table><thead><tr><th>MERCHANT</th><th>REGION</th><th>REVENUE</th><th>TRANSACTIONS</th><th>SUBSCRIBERS</th><th>GRADE</th></tr></thead><tbody>
            {data?.items.map((merchant) => <tr key={merchant.id}><td><Link className="merchant-link" to={`/merchants/${merchant.id}`}><span className="merchant-initial">{merchant.name.slice(0, 1)}</span><span>{merchant.name}<small>{merchant.code} · {merchant.category}</small></span></Link></td><td>{merchant.region}</td><td>₹{Number(merchant.revenue).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</td><td>{Number(merchant.transactions).toLocaleString("en-IN")}</td><td>{Number(merchant.subscribers).toLocaleString("en-IN")}</td><td><span className={`grade grade-${merchant.grade.replace("+", "plus")}`}>{merchant.grade}</span></td></tr>)}
            {!data?.items.length && <tr><td colSpan="6" className="table-empty">No merchants match these filters.</td></tr>}
          </tbody></table></div>}
        </div>
        <aside className="panel segment-panel"><div className="panel-heading"><div><h2>Performance leaders</h2><p>Top five by composite score</p></div></div>
          {(ranking?.top || []).map((merchant, index) => <Link className="leader-row" to={`/merchants/${merchant.id}`} key={merchant.id}><span className="leader-rank">0{index + 1}</span><span className="leader-info"><b>{merchant.name}</b><small>{merchant.region} · {merchant.category}</small></span><span className="leader-score">{merchant.score}</span></Link>)}
          <div className="grade-segments"><b>Portfolio segments</b>{(segments?.segments || []).map((segment) => <span key={segment.grade}><i className={`grade grade-${segment.grade.replace("+", "plus")}`}>{segment.grade}</i>{segment.count} merchants</span>)}</div>
          <div className="segment-note"><b>Score model</b><p>Revenue 40% · transactions 25% · subscribers 20% · growth 15%. Growth is neutral until a sufficient history is configured.</p></div>
        </aside>
      </section>
    </div>
  );
}
