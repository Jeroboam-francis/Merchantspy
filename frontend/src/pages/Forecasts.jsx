import { useState } from "react";
import TrendChart from "../components/TrendChart.jsx";
import { api } from "../services/api.js";
import "./Forecasts.css";

export default function Forecasts() {
  const [model, setModel] = useState("arima");
  const [periods, setPeriods] = useState(30);
  const [merchantId, setMerchantId] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function runForecast(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const query = new URLSearchParams({ model, periods: String(periods) });
      if (merchantId) query.set("merchant_id", merchantId);
      const response = await api(`/forecasts/revenue?${query}`, { method: "POST" });
      setResult(await response.json());
    } catch (failure) {
      setError(failure.message);
      setResult(null);
    } finally { setLoading(false); }
  }

  const series = Object.fromEntries((result?.forecast || []).map((row) => [row.target_date, row.predicted_revenue]));
  return (
    <div className="forecasts-page">
      <div className="page-heading"><div><p className="eyebrow">WORKSPACE / PREDICTIVE ANALYTICS</p><h1>Revenue forecasts</h1><p className="page-subtitle">Generate daily revenue forecasts with confidence bounds.</p></div></div>
      <form className="panel forecast-controls" onSubmit={runForecast}>
        <label>Forecast model<select value={model} onChange={(event) => setModel(event.target.value)}><option value="arima">ARIMA</option><option value="random_forest">Random Forest</option><option value="prophet">Prophet (optional dependency)</option></select></label>
        <label>Forecast horizon<select value={periods} onChange={(event) => setPeriods(Number(event.target.value))}><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option></select></label>
        <label>Merchant ID <input inputMode="numeric" placeholder="All merchants" value={merchantId} onChange={(event) => setMerchantId(event.target.value.replace(/\D/g, ""))} /></label>
        <button className="primary-button" disabled={loading}>{loading ? "Calculating…" : "Generate forecast"}</button>
      </form>
      {error && <div className="banner-error">{error}</div>}
      {result && <section className="forecast-results">
        <div className="panel"><TrendChart title={`${result.model} forecast`} subtitle={`${result.forecast.length} forecast days`} series={series} /></div>
        <div className="panel transaction-panel"><div className="panel-heading"><div><h2>Forecast detail</h2><p>Predicted revenue and model confidence range</p></div></div>
          <div className="table-scroll"><table><thead><tr><th>DATE</th><th>PREDICTED</th><th>LOWER</th><th>UPPER</th></tr></thead><tbody>
            {result.forecast.map((row) => <tr key={row.target_date}><td>{row.target_date}</td><td>₹{Number(row.predicted_revenue).toLocaleString("en-IN")}</td><td>₹{Number(row.lower_bound).toLocaleString("en-IN")}</td><td>₹{Number(row.upper_bound).toLocaleString("en-IN")}</td></tr>)}
          </tbody></table></div>
        </div>
      </section>}
      {!result && !error && <div className="forecast-empty panel"><span className="forecast-mark">⌁</span><h2>Plan with a forward view</h2><p>Select a model and horizon to forecast your revenue trajectory.</p></div>}
    </div>
  );
}
