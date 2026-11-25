import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { useApi } from "../hooks/useApi.js";
import { getJson } from "../services/api.js";
import networkMark from "../assets/merchant-network.svg";

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem("airtel_theme") === "dark");
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const { data: signals, error: signalsError } = useApi(() => getJson("/analytics/signals"), [], 300000);
  useEffect(() => {
    document.documentElement.classList.toggle("dark-theme", darkMode);
    localStorage.setItem("airtel_theme", darkMode ? "dark" : "light");
  }, [darkMode]);
  function signOut() {
    logout();
    navigate("/login");
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-title"><img src={networkMark} alt="" /><span className="brand-mark">airtel</span></span><span className="brand-caption">BUSINESS INTELLIGENCE</span></div>
        <div className="nav-caption">WORKSPACE</div>
        <nav className="side-nav">
          <NavLink to="/" end><span>◫</span> Executive dashboard</NavLink>
          <NavLink to="/analytics"><span>▥</span> Merchant analytics</NavLink>
          <NavLink to="/forecasts"><span>⌁</span> Revenue forecasts</NavLink>
        </nav>
        <div className="sidebar-bottom"><span className="status-dot" /> Data services operational</div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumb">Airtel <span>/</span> <b>Analytics workspace</b></div>
          <div className="topbar-actions"><div className="notification-control"><button className="theme-toggle" onClick={() => setNotificationsOpen((open) => !open)} aria-label="Open analytics notifications">♧ {signals?.anomalies?.length ?? "—"}</button>{notificationsOpen && <div className="notification-popover"><b>Analytics alerts</b>{signalsError ? <p>{signalsError}</p> : (signals?.anomalies || []).length ? signals.anomalies.slice(0, 5).map((signal) => <p key={`${signal.date}-${signal.value}`}>Revenue anomaly · {signal.date} · ₹{Number(signal.value).toLocaleString("en-IN")}</p>) : <p>No revenue anomalies detected.</p>}</div>}</div><button className="theme-toggle" onClick={() => setDarkMode((value) => !value)} aria-label="Toggle dark mode">{darkMode ? "☼" : "◐"}</button><span className="role-pill">{user?.role || "viewer"}</span><span className="user-avatar">{user?.full_name?.slice(0, 1) || "A"}</span><span className="user-name">{user?.full_name || "Analyst"}</span><button className="text-button" onClick={signOut}>Sign out</button></div>
        </header>
        <div className="page-content"><Outlet context={{ signals, signalsError }} /></div>
      </main>
    </div>
  );
}
